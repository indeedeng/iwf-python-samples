import traceback

from random import randint
from flask import Flask, request
from iwf.iwf_api.models import (
    WorkflowStateExecuteRequest,
    WorkflowStateWaitUntilRequest,
    WorkflowWorkerRpcRequest,
)
from iwf.worker_service import (
    WorkerService,
)

from iwf_config import client, worker_service
from controller_workflow import (
    ControllerWorkflow,
    NUM_CONTROLLER_WORKFLOWS,
    Request
)
from iwf.errors import WorkflowNotExistsError
from processing_workflow import ProcessingWorkflow

flask_app = Flask(__name__)


# http://localhost:8802/controller/request?id=123
@flask_app.route("/controller/request")
def signup_submit():
    id = request.args["id"]
    req = Request(id=id, data="abcd")

    rand_suffix = randint(1, NUM_CONTROLLER_WORKFLOWS)
    controller_workflow_id = f"controller_workflow_{rand_suffix}" # replace by other mechanism to choose resource
    try:
        client.invoke_rpc(controller_workflow_id, ControllerWorkflow.enqueue, req)
    except WorkflowNotExistsError:
        client.start_workflow(ControllerWorkflow, controller_workflow_id, 0, req)
    return "request is accepted"


# http://localhost:8802/controller/processing/describe?id=123
@flask_app.route("/controller/processing/describe")
def signup_describe():
    id = request.args["id"]
    child_workflow_id = f"processing-{id}"
    return client.invoke_rpc(child_workflow_id, ProcessingWorkflow.describe)


@flask_app.route("/")
def index():
    return "iwf workflow home"


# below are iWF workflow worker APIs to be called by iWF server


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


# this handler is extremely useful for debugging iWF
# the WebUI will be able to show you the error with stacktrace
@flask_app.errorhandler(Exception)
def internal_error(exception):
    return worker_service.handle_worker_error(exception), 500


def main():
    flask_app.run(host="0.0.0.0", port=8802)


if __name__ == "__main__":
    main()
