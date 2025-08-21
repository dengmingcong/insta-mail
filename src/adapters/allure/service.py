import json
from pathlib import Path
from urllib.parse import urlparse


class StepExtractor(object):
    """Extractor for one step of testcase.

    :var step: One step of testcase in allure JSON data.
    :vartype step: dict
    :var attachments_path: Path to directory containing all attachments.
    :vartype attachments_path: Path
    :var name: Name of the step.
    :vartype name: str
    :var status: Status of the step.
    :vartype status: str
    :var http_requests:
        List of HTTP requests made in the step, in a specific format.

        Example::

            [
                {
                    "step_name": "some text",
                    "step_status": "passed"
                    "attachment_uid": "c68ed3f719b6685b",  # same uid means reference to the same file
                    "urls": ["https://local-ci-smartapi.vesync.com/cloud/v1/user/isAccountExist"],
                    "duration": 153.0,
                }
            ]

    :vartype http_requests: list[dict]
    :var attachments_mapping: Mapping of attachment names to their JSON data.
    :vartype attachments_mapping: dict
    """

    def __init__(self, step: dict, attachments_path: Path):
        """Init an object.

        :param step: One step of testcase in allure JSON data.
        :param attachments_path: Path to directory containing all attachments,
            by default, it's ``allure-report/data/attachments``,

            .. note::
                Testcase JSON files save attachment references only, they don't save attachment content.
        """
        self.step: dict = step
        self.attachments_path: Path = attachments_path

        self.name: str = step["name"]
        self.status: str = step["status"]

        self.http_requests: list[dict] = []
        self.attachments_mapping: dict = self.convert_attachments_to_mapping()

    def convert_attachments_to_mapping(self) -> dict:
        """Convert list of attachments to mapping (name -> attachment)."""
        # It is assumed that attachment names are unique.
        attachments_mapping = {}

        for attachment in self.step["attachments"]:
            attachment_name: str = attachment["name"]

            # Canonicalize attachment with name `request *` to `request`,
            # `request *` attachment is supposed to contain http request.
            if attachment_name.startswith("request"):
                attachment_name = "request"

            attachments_mapping[attachment_name] = attachment
        return attachments_mapping

    def extract_from_request_attachment(self) -> None:
        """Extract http request from attachment ``request``.

        .. note::
            Response time (duration) will be extracted too.

        Given request attachment::

            {
                "uid":"297fd70bbc835fb3",
                "name":"request 🕒 2023-08-10 17:04:35 UTC+08:00",
                "source":"297fd70bbc835fb3.json",
                "type":"application/json",
                "size":526
            }

        Got::

            uid: 297fd70bbc835fb3
            url: read from file `297fd70bbc835fb3.json`
        """
        request_attachment = self.attachments_mapping["request"]

        # Load request attachment.
        with open(
            self.attachments_path / request_attachment["source"], "r", encoding="utf-8"
        ) as f:
            request_attachment_data = json.load(f)

        # Get url from request attachment.
        url = request_attachment_data["url"]

        # For firmware apis, replace url with api method.
        # Redirection won't happen for firmware api, so this logic was just implemented in request.
        parsed_url = urlparse(url)
        if parsed_url.path.startswith("/device") and "simulator" in parsed_url.netloc:
            # Fix AttributeError when body exists but corresponding value is ``None``.
            if "body" in request_attachment_data and isinstance(
                (body := request_attachment_data["body"]), dict
            ):
                context = body.get("context", {})
                if method := context.get("method"):
                    url = method
                else:
                    url = "UNKNOWN_FIRMWARE_API"
            else:
                url = "UNKNOWN_FIRMWARE_API"

        # Get duration (response_time_ms) from `statistics` attachment.
        if statistics_attachment := self.attachments_mapping.get("statistics"):
            with open(
                self.attachments_path / statistics_attachment["source"],
                "r",
                encoding="utf-8",
            ) as f:
                duration = json.load(f)["response_time_ms"]

        self.http_requests.append(
            {
                "step_name": self.name,
                "step_status": self.status,
                "attachment_uid": request_attachment["uid"],
                "urls": [url],
                "duration": duration,
            }
        )

    def extract_from_session_data_attachment(self) -> None:
        """Extract http request from attachment ``session data``.

        Session data attachment means redirection occurs, and thus multiple requests were sent.
        """
        session_data_attachment: dict = self.attachments_mapping.get("session data", {})

        with open(
            self.attachments_path / session_data_attachment["source"],
            "r",
            encoding="utf-8",
        ) as f:
            session_data_attachment_data = json.load(f)

        self.http_requests.append(
            {
                "step_name": self.name,
                "step_status": self.status,
                "attachment_uid": session_data_attachment["uid"],
                "duration": session_data_attachment_data["stat"]["response_time_ms"],
                "urls": [
                    req_resp["request"]["url"]
                    for req_resp in session_data_attachment_data["req_resps"]
                ],
            }
        )

    def extract(self) -> None:
        """Extract http requests from step."""
        # Extract http requests from step self.
        if self.step["attachments"]:
            if "request" in self.attachments_mapping:
                self.extract_from_request_attachment()
            elif "session data" in self.attachments_mapping:
                self.extract_from_session_data_attachment()

        # Extract http requests from sub-steps.
        for sub_step in self.step["steps"]:
            sub_step_extractor = StepExtractor(sub_step, self.attachments_path)
            sub_step_extractor.extract()
            self.http_requests.extend(sub_step_extractor.http_requests)


class TestCaseExtractor(object):
    """Extractor for each file under `allure-report/data/test-cases`."""

    def __init__(self, testcase: dict, attachments_path: Path):
        """
        Init an object.

        Example of http_requests:
        [
            {
                "step_name": "some text",
                "step_status": "passed"
                "attachment_uid": "c68ed3f719b6685b",  # same uid means reference to the same file
                "urls": ["https://local-ci-smartapi.vesync.com/cloud/v1/user/isAccountExist"],
                "duration": 153.0,
            }
        ]

        :param testcase: data read from one JSON file under `allure-report/data/test-cases`
        :param attachments_path: path to directory containing attachments (default: `allure-report/data/attachments`)
            testcase JSON files save attachment references only, they don't save attachment content.
        """
        self.testcase = testcase
        self.attachments_path = attachments_path

        self.name = testcase["name"]
        self.fullname = testcase["fullName"]
        self.status = testcase["status"]
        self.parameters = testcase["parameters"]
        self.http_requests = []

    def extract(self):
        """Extract http requests from all three stages."""
        steps = (
            self.testcase.get("beforeStages", [])  # each item of beforeStages is a step
            + self.testcase.get("testStage", {}).get(
                "steps", []
            )  # each item of testStage["steps"] is a step
            + self.testcase.get("afterStages", [])  # each item of afterStages is a step
        )
        for step in steps:
            step_extractor = StepExtractor(step, self.attachments_path)
            step_extractor.extract()
            self.http_requests.extend(step_extractor.http_requests)


class ReportExtractor(object):
    """Extractor for allure report."""

    def __init__(self, allure_report_home: Path):
        """
        Init an object.

        :param allure_report_home: path to allure report
        """
        self.allure_report_home = allure_report_home
        self.testcase_dir = allure_report_home / "data" / "test-cases"
        self.attachments_path = allure_report_home / "data" / "attachments"

        self.testcases = []

    def extract(self):
        """Extract http requests from all testcases of report."""
        for testcase_file in self.testcase_dir.iterdir():
            with open(testcase_file, "r", encoding="utf-8") as f:
                testcase = json.load(f)
                testcase_extractor = TestCaseExtractor(testcase, self.attachments_path)
                testcase_extractor.extract()
                self.testcases.append(
                    {
                        "name": testcase_extractor.name,
                        "fullname": testcase_extractor.fullname,
                        "status": testcase_extractor.status,
                        "parameters": testcase_extractor.parameters,
                        "http_requests": testcase_extractor.http_requests,
                    }
                )


def is_intermediate_retry_request(name: str) -> bool:
    """Return True if name is intermediate retry request."""
    # report successful step always
    if "✔️" in name:
        return False
    # either success emoji or failure emoji must be in name if it is a retrying step
    elif "❌" not in name:
        return False
    # retrying step must start with `first request` or `retry: `
    elif not (name.startswith("first request") or name.startswith("retry: ")):
        return False
    # stopping retrying step must contain `last retry` or `the condition to stop retrying was met`
    elif "last retry" in name or "the condition to stop retrying was met" in name:
        return False
    else:
        return True


class ApiStat(object):
    """Make statistics on api and testcase."""

    def __init__(self, allure_report_home: Path):
        self.allure_report_home = allure_report_home
        self.extractor = ReportExtractor(allure_report_home)
        self.extractor.extract()
        self.stat_data = {"testcases": [], "apis": {}}

    def stat(self) -> None:
        """Make statistics on api and testcase.

        Examples:
        ```python
        s = ApiStat(...)
        s.stat(...)
        s.stat_data

        # output
        {
            "testcases": [
                {
                    "name": "testcase name",
                    "fullname": "tests.postman_echo.retry_on_failure_test.TestRetryOnFailure#test_start",
                    "status": "failed",
                    "parameters": [],
                    "apis": [
                        {"url": "https://postman-echo.com/foo", "duration": 100},
                        {"url": "https://postman-echo.com/bar", "duration": 200},
                    ],
                }
            ],
            "apis": {
                "https://postman-echo.com/post": 7
            },
        }
        ```
        """
        global_attachment_uid_records = []

        for testcase in self.extractor.testcases:
            testcase_stat = {
                "name": testcase["name"],
                "fullname": testcase["fullname"],
                "status": testcase["status"],
                "parameters": testcase["parameters"],
                "apis": [],
            }
            # subset of global_attachment_uid_records
            testcase_attachment_uid_records = []

            for http_request in testcase["http_requests"]:
                # ------ STEP: 1 stat from perspective of testcase ------
                # parametrized testcases will be counted multiple times.
                if (
                    attachment_uid := http_request["attachment_uid"]
                ) in testcase_attachment_uid_records:
                    continue

                testcase_attachment_uid_records.append(attachment_uid)

                # only count the first request if redirection occurs
                testcase_stat["apis"].append(
                    {
                        "url": http_request["urls"][0],
                        "duration": http_request["duration"],
                    }
                )

                # ------ STEP: 2 stat from perspective of api ------
                if attachment_uid in global_attachment_uid_records:
                    continue

                global_attachment_uid_records.append(attachment_uid)

                # only count the first request if redirection occurs
                api_url = http_request["urls"][0]
                count = self.stat_data["apis"].get(api_url, 0)
                self.stat_data["apis"][api_url] = count + 1

            self.stat_data["testcases"].append(testcase_stat)
