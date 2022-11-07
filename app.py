import os
import base64
import requests
import diff_match_patch
from flask import Flask, request

app = Flask(__name__)


def app_headers():
    headers = {"Authorization": "Bearer {}".format(os.environ.get("GH_TOKEN"))
               }
    return headers


dmp = diff_match_patch.diff_match_patch()


@app.route("/", methods=["GET"])
def home():
    return """
    <html>
        <script>
            function redirect(){       
                window.location.href="http://127.0.0.1:5000/embedding?link=" + document.getElementById("githubLink").value;              
            }
        </script>
        <form onsubmit="redirect(); return false;" method="get" action="">  
            Github Link to a commit: <input id="githubLink" type="text"></input>
            <input type="submit"/>  
        </form>
    </html>
    """


IGNORE_EXTENSIONS = ["pyc"]


@app.route("/embedding", methods=['GET'])
def get_embedding():
    github_link = request.args.get("link")
    path = github_link[github_link.index('github.com/')+len('github.com/'):]
    owner = path.split("/")[0]
    repo = path.split("/")[1]
    commit = github_link.split("/")[-1]
    github_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit}"
    response = requests.get(github_api_url, headers=app_headers())
    if response.status_code != 200:
        return "<h1>GitHub Rate Limit</h1>"
    json_response = response.json()

    parent_commit = None
    if len(json_response["parents"]) > 1:
        raise Exception("Length of parents is greater than 1")
    elif len(json_response["parents"]) == 1:
        parent = json_response["parents"][0]
        parent_url = parent["url"]
        parent_commit = requests.get(
            parent_url, headers=app_headers()).json()["sha"]

    final_html = ""
    for file in json_response["files"]:
        filename = file['filename']
        if filename.split(".")[-1] in IGNORE_EXTENSIONS:
            continue
        prev_file_response = None
        if parent_commit:
            prev_commit_file_url = f"{file['contents_url'][:file['contents_url'].index('?ref=') + 5]}{parent_commit}"
            prev_file_response = requests.get(
                prev_commit_file_url, headers=app_headers())
        current_commit_file_url = file["contents_url"]
        prev_file_contents = ""
        if prev_file_response and prev_file_response.status_code == 200:
            prev_file_contents = base64.b64decode(
                prev_file_response.json()["content"]).decode("utf-8")

        current_file_response = requests.get(
            current_commit_file_url, headers=app_headers())
        current_file_contents = ""
        if current_file_response.status_code == 200:
            current_file_contents = base64.b64decode(
                current_file_response.json()["content"]).decode("utf-8")

        d = dmp.diff_main(prev_file_contents, current_file_contents)
        dmp.diff_cleanupSemantic(d)
        final_html += f"<h2>{filename}</h2><pre>{dmp.diff_prettyHtml(d).replace('&para;', '')}</pre>"
        final_html += f"<br>"

    style = "<style>pre { font-family: -apple-system,BlinkMacSystemFont,\"Segoe UI\",Helvetica,Arial,sans-serif,\"Apple Color Emoji\",\"Segoe UI Emoji\"; }</style>"
    return f"{style}{final_html}"


if __name__ == "__main__":
    app.run()
