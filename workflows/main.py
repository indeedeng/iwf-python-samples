import traceback

from flask import Flask, request
from iwf.iwf_api.models import (
    WorkflowStateExecuteRequest,
    WorkflowStateWaitUntilRequest,
    WorkflowWorkerRpcRequest,
)
from iwf.worker_service import (
    WorkerService,
)

from workflows.iwf_config import client, worker_service
from workflows.signup_workflow import BasicWorkflow

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return "iwf workflow worker home"


@flask_app.route(WorkerService.api_path_workflow_state_wait_until, methods=["POST"])
def handle_wait_until():
    req = WorkflowStateWaitUntilRequest.from_dict(request.json)
    resp = worker_service.handle_workflow_state_wait_until(req)
    return resp.to_dict()


@flask_app.route(WorkerService.api_path_workflow_state_execute, methods=["POST"])
def handle_execute():
    req = WorkflowStateExecuteRequest.from_dict(request.json)
    resp = worker_service.handle_workflow_state_execute(req)
    return resp.to_dict()


@flask_app.route(WorkerService.api_path_workflow_worker_rpc, methods=["POST"])
def handle_rpc():
    req = WorkflowWorkerRpcRequest.from_dict(request.json)
    resp = worker_service.handle_workflow_worker_rpc(req)
    return resp.to_dict()


@flask_app.errorhandler(Exception)
def internal_error(exception):
    response = exception.get_response()
    # replace the body with JSON
    response.data = traceback.format_exc()
    response.content_type = "application/json"
    response.status_code = 500
    return response


@flask_app.route("/test")
def endpoint():
    client.start_workflow(BasicWorkflow, "test", 10, 100)
    return "hello"


def main():
    flask_app.run(host="0.0.0.0", port=8802)


if __name__ == "__main__":
    main()
