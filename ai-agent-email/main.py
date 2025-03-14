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

from ai_agent_workflow import EmailAgentWorkflow
from iwf_config import client, worker_service

flask_app = Flask(__name__)


# http://localhost:8802/api/ai-agent/start?workflowId="test"
@flask_app.route("/api/ai-agent/start")
def ai_agent_start():
    wf_id = request.args["workflowId"]
    client.start_workflow(EmailAgentWorkflow, wf_id, 86400)
    return "workflow started"


# http://localhost:8802/api/ai-agent/request?workflowId="test"&request="help me write an email to qlong.seattle@gmail.com to say thank you"
@flask_app.route("/api/ai-agent/request")
def ai_agent_request():
    wf_id = request.args["workflowId"]
    req = request.args["request"]
    resp = client.invoke_rpc(wf_id, EmailAgentWorkflow.send_request, req)
    return "{0}".format(resp)


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
    print(traceback.format_exc())
    return traceback.format_exc(), 500


def main():
    flask_app.run(host="0.0.0.0", port=8802)


if __name__ == "__main__":
    main()
