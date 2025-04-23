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

from basic.basic_workflow import BasicWorkflow
from basic.iwf_config import client, worker_service

flask_app = Flask(__name__)


# http://localhost:8802/basic/start?workflowId=test-1108&inputNum=4
@flask_app.route("/basic/start")
def basic_start():
    workflow_id = request.args["workflowId"]
    input_num = request.args["inputNum"]

    run_id = client.start_workflow(BasicWorkflow, workflow_id, 3600, int(input_num))
    return run_id

# http://localhost:8802/basic/appendString?workflowId=test-1108&str=test
@flask_app.route("/basic/appendString")
def basic_append_string():
    workflow_id = request.args["workflowId"]
    st = request.args["str"]
    client.invoke_rpc(workflow_id, BasicWorkflow.append_string, st)
    return st

# http://localhost:8802/basic/approve?workflowId=test-1108
@flask_app.route("/basic/approve")
def basic_approve():
    workflow_id = request.args["workflowId"]
    client.invoke_rpc(workflow_id, BasicWorkflow.approve)
    return "done"

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
    return traceback.format_exc(), 500


def main():
    flask_app.run(host="0.0.0.0", port=8802)


if __name__ == "__main__":
    main()
