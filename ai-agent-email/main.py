import smtplib
import time
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
from openai import OpenAI

from moneytransfer.iwf_config import client, worker_service
from moneytransfer.money_transfer_workflow import TransferRequest, MoneyTransferWorkflow

flask_app = Flask(__name__)


# http://localhost:8802/moneytransfer/start?fromAccount=long&toAccount=github&amount=10&notes=testnotest
@flask_app.route("/moneytransfer/start")
def money_transfer_start():
    from_account = request.args["fromAccount"]
    to_account = request.args["toAccount"]
    amount = request.args["amount"]
    notes = request.args["notes"]
    transfer_request = TransferRequest(from_account, to_account, int(amount), notes)

    client.start_workflow(MoneyTransferWorkflow, "money_transfer" + str(time.time()), 3600, transfer_request)
    return "workflow started"


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
    client = OpenAI()

    response = client.responses.create(
        model="gpt-4o",
        input="Tell me a three sentence bedtime story about a unicorn."
    )

    from agents import Agent, Runner

    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)

    YOUR_GOOGLE_EMAIL = 'prclqz@gmail.com'  # The email you setup to send the email using app password
    YOUR_GOOGLE_EMAIL_APP_PASSWORD = 'pmsy hngl aiok tlch'  # The app password you generated

    smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtpserver.ehlo()
    smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)

    # Test send mail
    sent_from = YOUR_GOOGLE_EMAIL
    sent_to = sent_from  # Send it to self (as test)
    email_text = 'This is a test'
    smtpserver.sendmail(sent_from, sent_to, email_text)

    # Close the connection
    smtpserver.close()

    # main()
