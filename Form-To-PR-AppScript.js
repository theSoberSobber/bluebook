// make sure to give permission by manual exec once
// make sure to add GH_TOKEN property, make sure your token is properly scoped
const USERNAME = "theSoberSobber";
const REPO = "bluebook";

function onSubmit(e) {
    var form = FormApp.getActiveForm();
    var allResponses = form.getResponses();
    var latestResponse = allResponses[allResponses.length - 1];
    var response = latestResponse.getItemResponses();

    var payload = {};

    var allItems = form.getItems();

    for (var i = 0; i < allItems.length; i++) {
        var questionTitle = allItems[i].getTitle();
        var answer = null;

        var itemResponse = response.find(function(item) {
            return item.getItem().getTitle() === questionTitle;
        });

        if (itemResponse) {
          if (itemResponse.getItem().getType() === FormApp.ItemType.FILE_UPLOAD) {
              var files = itemResponse.getResponse();
              answer = files ? files.map(function(fileId) {
                  var fileUrl = `https://drive.google.com/file/d/${fileId}/view?usp=sharing`;
                  makeFilePublic(fileId);
                  return `[https://drive.google.com/file/d/${fileId}/view?usp=sharing](https://drive.google.com/file/d/${fileId}/view?usp=sharing)`;
              }) : [];
          } else {
              answer = itemResponse.getResponse();
          }
        }


        payload[questionTitle] = answer ? (Array.isArray(answer) ? answer : [answer]) : [];
    }

    var responseId = allResponses.length;
    var date = new Date().toISOString().split('T')[0];

    var fileName = `response_${responseId}_${date}.json`;

    var responseData = {
        "timestamp": new Date().toISOString(),
        "email": latestResponse.getRespondentEmail(),
        "data": payload
    };

    var fileContent = JSON.stringify(responseData, null, 2);

    var GITHUB_TOKEN = PropertiesService.getScriptProperties().getProperty("GH_TOKEN");

    createGitHubFile(fileName, fileContent, responseId, GITHUB_TOKEN);
}

function makeFilePublic(fileId) {
    var driveService = DriveApp.getFileById(fileId); // Get the file by ID
    driveService.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW); // Set the sharing to public with view access
}

function createGitHubFile(fileName, fileContent, responseId, GITHUB_TOKEN) {
    var branchName = fileName;
    var defaultBranch = 'main';

    var url = `https://api.github.com/repos/${USERNAME}/${REPO}/git/refs/heads/${defaultBranch}`;

    var options = {
        "method": "get",
        "headers": {
            "Authorization": "token " + GITHUB_TOKEN
        }
    };

    try {
        var response = UrlFetchApp.fetch(url, options);
        var defaultBranchData = JSON.parse(response.getContentText());
        var sha = defaultBranchData.object.sha;

        var createBranchUrl = `https://api.github.com/repos/${USERNAME}/${REPO}/git/refs`;
        var createBranchPayload = {
            "ref": `refs/heads/${branchName}`,
            "sha": sha
        };

        var createBranchOptions = {
            "method": "post",
            "headers": {
                "Authorization": "token " + GITHUB_TOKEN
            },
            "payload": JSON.stringify(createBranchPayload)
        };

        UrlFetchApp.fetch(createBranchUrl, createBranchOptions);

        var createCommitUrl = `https://api.github.com/repos/${USERNAME}/${REPO}/contents/responses/${fileName}`;
        var commitPayload = {
            "message": `[Webhook] Response ${responseId}: ${new Date().toISOString()}`,
            "content": Utilities.base64Encode(fileContent),
            "branch": branchName
        };

        var commitOptions = {
            "method": "put",
            "headers": {
                "Authorization": "token " + GITHUB_TOKEN
            },
            "payload": JSON.stringify(commitPayload)
        };

        UrlFetchApp.fetch(createCommitUrl, commitOptions);

        var createPRUrl = `https://api.github.com/repos/${USERNAME}/${REPO}/pulls`;
        var prPayload = {
            "title": `Response ${responseId}`,
            "head": branchName,
            "base": defaultBranch,
            "body": `This PR contains the response data for response ID ${responseId}`
        };

        var prOptions = {
            "method": "post",
            "headers": {
                "Authorization": "token " + GITHUB_TOKEN
            },
            "payload": JSON.stringify(prPayload)
        };

        UrlFetchApp.fetch(createPRUrl, prOptions);
        Logger.log("PR created successfully: " + fileName);
    } catch (e) {
        Logger.log("Error: " + e.toString());
    }
}
