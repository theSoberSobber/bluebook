function processProxyEmails() {
  const threads = GmailApp.search('is:starred');

  for (const thread of threads) {
    const messages = thread.getMessages();

    for (const message of messages) {
      if (message.isStarred()) {
        try {
          const sender = message.getFrom();
          const body = message.getBody();
          
          const acInEmail = extractAcInEmail(sender);
          const proxyEmail = extractProxyEmail(body);

          console.log(acInEmail);
          console.log(proxyEmail);
          
          if (!proxyEmail) {
            sendErrorEmail(message, "No Proxy Email Found in Your Email, please send the email again with the other email written in the body of the email.");
            message.unstar();
            continue;
          }

          const githubToken = PropertiesService.getScriptProperties().getProperty('GH_TOKEN');
          const repoOwner = 'theSoberSobber';
          const repoName = 'bluebook';
          const filePath = 'authorized_external_emails.json';
          const branch = 'emails';

          let authorizedEmails;
          try {
            const currentContent = getFileContentFromGitHub(githubToken, repoOwner, repoName, filePath, branch);
            authorizedEmails = JSON.parse(currentContent);
          } catch (error) {
            if (error.toString().includes('404')) {
              authorizedEmails = {};
            } else {
              throw error;
            }
          }

          console.log(authorizedEmails);

          if (authorizedEmails[acInEmail]) {
            sendAlreadyRegisteredEmail(message, authorizedEmails[acInEmail]);
            message.unstar();
            continue;
          }

          authorizedEmails[acInEmail] = proxyEmail;

          const updatedContentBase64 = Utilities.base64Encode(JSON.stringify(authorizedEmails, null, 2));
          updateGitHubFile(
            githubToken, 
            repoOwner, 
            repoName, 
            filePath, 
            branch, 
            updatedContentBase64, 
            `Add proxy email for ${acInEmail}`
          );

          // Update Google Form regex
          updateGoogleFormEmailValidation(authorizedEmails);

          sendConfirmationEmail(message, proxyEmail);

          message.unstar();

        } catch (error) {
          sendErrorEmail(message, `Processing error: ${error.toString()}`);
          message.unstar();
        }
      }
    }
  }
}

function extractAcInEmail(sender) {
  const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.ac\.in)/;
  const match = sender.match(emailRegex);
  return match ? match[1] : null;
}

function extractProxyEmail(body) {
  const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/;
  const match = body.match(emailRegex);
  return match ? match[1] : null;
}

function sendAlreadyRegisteredEmail(originalMessage, existingProxyEmail) {
  const sender = extractAcInEmail(originalMessage.getFrom());
  GmailApp.sendEmail(
    sender,
    'Proxy Email Already Registered',
    `A proxy email (${existingProxyEmail}) has already been registered for this account. Please use this email for your submissions.`
  );
}

function sendConfirmationEmail(originalMessage, proxyEmail) {
  const sender = extractAcInEmail(originalMessage.getFrom());
  GmailApp.sendEmail(
    sender,
    'Proxy Email Registered Successfully',
    `Your proxy email (${proxyEmail}) has been registered and can now be used for submissions.`
  );
}

function sendErrorEmail(originalMessage, errorMessage) {
  console.log(errorMessage);
  const sender = extractAcInEmail(originalMessage.getFrom());
  GmailApp.sendEmail(
    sender,
    'Error Processing Proxy Email',
    errorMessage
  );
}

function getFileContentFromGitHub(token, owner, repo, path, branch) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=${branch}`;
  const headers = {
    'Authorization': `token ${token}`,
    'Accept': 'application/vnd.github.v3+json'
  };
  
  const response = UrlFetchApp.fetch(url, { headers: headers });
  const fileInfo = JSON.parse(response.getContentText());
  let decoded = Utilities.base64Decode(fileInfo.content, Utilities.Charset.UTF_8);
  return Utilities.newBlob(decoded).getDataAsString();
}

function updateGitHubFile(token, owner, repo, path, branch, contentBase64, commitMessage) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
  
  let sha = null;
  try {
    const getUrl = `${url}?ref=${branch}`;
    const getHeaders = {
      'Authorization': `token ${token}`,
      'Accept': 'application/vnd.github.v3+json'
    };
    const getResponse = UrlFetchApp.fetch(getUrl, { headers: getHeaders });
    const currentFile = JSON.parse(getResponse.getContentText());
    sha = currentFile.sha;
  } catch (error) {
    console.log(error.toString(), error.toString().includes('404'));
    if (!error.toString().includes('404')) {
      console.log("mai fek raha hu bhai error");
      throw error;
    }
  }

  const payload = {
    message: commitMessage,
    content: contentBase64,
    branch: branch
  };

  if (sha) payload.sha = sha;

  const headers = {
    'Authorization': `token ${token}`,
    'Accept': 'application/vnd.github.v3+json'
  };

  const options = {
    method: 'put',
    headers: headers,
    payload: JSON.stringify(payload)
  };
  try {
    UrlFetchApp.fetch(url, options);
  } catch(error){
    throw error;
  }
}

function getFullRegex(authorizedEmails){
    let emailRegex = '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.ac\\.in';
    if(Object.keys(authorizedEmails).length === 0){
      emailRegex+='$';
      return emailRegex;
    }
    let literalEmails = Object.values(authorizedEmails).map(email => `^${email.replace('.', '\\.')}$`).join('|');
    const fullRegex = emailRegex + '|' + literalEmails;
    return fullRegex;
}

function updateGoogleFormEmailValidation(authorizedEmails) {
  const fullRegex = getFullRegex(authorizedEmails);

  console.log(fullRegex);

  const formId = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  const form = FormApp.openById(formId);

  const items = form.getItems(FormApp.ItemType.TEXT);
  let emailField = null;
  
  for (const item of items) {
    const textItem = item.asTextItem();
    if (textItem.getTitle().toLowerCase().includes('email')) {
      emailField = textItem;
      break;
    }
  }

  console.log(emailField);
 
  if (emailField) {
    const emailValidation = FormApp.createTextValidation()
      .requireTextMatchesPattern(fullRegex)
      .build();
    emailField.setValidation(emailValidation);
    Logger.log('Email validation updated successfully!');
  }
}
