Qualtrics.SurveyEngine.addOnload(function () {
	/*Place your JavaScript here to run when the page loads*/

	////////////////////////////////////////////////////////////////
	// Key embedded data from the Qualtrics survey flow setup    ///
	////////////////////////////////////////////////////////////////

	// Instructions: Initialize these variables in the survey flow.
	// `interview_id` is set by the interviewer-selection question (select_interviewer.js).
	var userID = Qualtrics.SurveyEngine.getEmbeddedData('user_id');
	var interviewID = Qualtrics.SurveyEngine.getEmbeddedData('interview_id');
	var endpoint = Qualtrics.SurveyEngine.getEmbeddedData('interview_endpoint');

	////////////////////////////////
	// Key input and output elements
	////////////////////////////////
	var chatArea = document.getElementById("chatArea");
	var submitButton = document.getElementById("submitButton");
	var inputField = document.getElementById("inputBox");
	var instructionText = document.getElementById("instructionText");

	////////////////////////////////////////////////////
	// Interface language follows the interview config //
	////////////////////////////////////////////////////
	var german = typeof interviewID === "string" && interviewID.slice(-3) === "_DE";
	var TEXT = german ? {
		placeholder: "Schreiben Sie hier Ihre Antwort...",
		instruction: "Bitte antworten Sie in ganzen Sätzen.",
		submit: "Antwort senden",
		waiting: "Warte auf Antwort...",
		end: "Ende des Interviews",
		errorStart: "Es ist ein technischer Fehler aufgetreten. Bitte laden Sie die Seite neu oder fahren Sie mit der Umfrage fort.",
		errorNext: "Es ist ein technischer Fehler aufgetreten. Bitte versuchen Sie es erneut."
	} : {
		placeholder: "Type your message here...",
		instruction: "Please write full sentences.",
		submit: "Submit response",
		waiting: "Waiting for reply...",
		end: "End of interview",
		errorStart: "There was a technical error. Please refresh or proceed in the survey.",
		errorNext: "There was a technical error. Please try again."
	};
	inputField.placeholder = TEXT.placeholder;
	instructionText.innerText = TEXT.instruction;
	submitButton.innerText = TEXT.submit;

	///////////////////////////////////////////
	/// ADD NEW MESSAGES WITH DANCING DOTS ////
	///////////////////////////////////////////

	function appendChatbotMessage(message, chatArea, status) {
		// New message from the chatbot
		var messageContent = document.createElement('div');
		messageContent.style.cssText = "word-wrap: break-word; width: 80%; border: 1px solid #F6F6F6; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #F6F6F6; display: block; margin-right: auto;  font-size: 18px; line-height: 1.5;";

		if (status === "waiting") {
			// Dancing dots animation
			messageContent.innerHTML = `
			<div word-wrap: break-word; width: 80%; border: 1px solid #F6F6F6; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #F6F6F6; display: block; margin-right: auto;>
			<div id="wave" style="position:relative; vertical-align: center text-align:left"; text-align:center;">
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite;"></span>
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -1.1s;"></span>
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -0.9s;"></span>
			</div><style>@keyframes wave {0%, 60%, 100% {transform: initial;} 30% {transform: translateY(-7px);}}</style></div>`;
			messageContent.id = "dancingDots";
		} else if (status === "response") {
			var existingDots = document.getElementById("dancingDots");
			if (existingDots) {
				existingDots.innerText = message.trim();
				existingDots.removeAttribute('id');
				chatArea.scrollTop = chatArea.scrollHeight;
				return; // Since the message is replaced, we don't need to append anything new
			} else {
				messageContent.innerText = message.trim();
			}
		}
		chatArea.appendChild(messageContent);
		chatArea.scrollTop = chatArea.scrollHeight;
	}

	// Make a missing survey-flow setup visible during testing instead of failing silently.
	if (!userID || !interviewID || !endpoint) {
		appendChatbotMessage("Setup error: embedded data missing (user_id=" + userID + ", interview_id=" + interviewID + ", interview_endpoint=" + endpoint + ").", chatArea, "response");
		submitButton.disabled = true;
		return;
	}

	////////////////////////////////////////////
	// GET THE FIRST QUESTION FROM THE SERVER //
	////////////////////////////////////////////
	jQuery.ajax({
		url: endpoint,
		timeout: 60000,
		type: "POST",
		data: JSON.stringify({
			route: "next",
			payload: {
				user_message: "",
				session_id: userID,
				interview_id: interviewID
			}
		}),
		contentType: "application/json",
		dataType: "json",
		success: function (data) {
			var question = data.message.trim();
			appendChatbotMessage(question, chatArea, "response");
			Qualtrics.SurveyEngine.setEmbeddedData('first_question', question);
		},
		error: function (jqXHR, textStatus, errorThrown) {
			console.error("Error:", errorThrown);
			appendChatbotMessage(TEXT.errorStart, chatArea, "response");
		}
	});

	////////////////////////////////////////////////////////////
	// Prevent copy, cut, and paste in chatArea and inputField /
	////////////////////////////////////////////////////////////
	["copy", "cut", "paste"].forEach(eventType => {
		[chatArea, inputField].forEach(element => {
			element.addEventListener(eventType, event => {
				event.preventDefault();
			});
		});
	});

	////////////////////////////////////////////////////////////
	// GENERATE THE NEXT QUESTION ON SUBMIT BUTTON CLICK ///////
	////////////////////////////////////////////////////////////
	submitButton.addEventListener("click", function () {
		var userMessage = inputField.value.trim();
		// Take action only for non-empty messages.
		if (userMessage) {
			// Clear the input field
			inputField.value = "";

			// Make the submit button unclickable until the chatbot replies
			submitButton.disabled = true;
			submitButton.style.backgroundColor = '#ccc';
			submitButton.innerText = TEXT.waiting;

			// Add user message to the chat area
			var messageContent = document.createElement('div');
			messageContent.style.cssText = "display: inline-block; max-width: 80%; border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #ddd; word-wrap: break-word; white-space: pre-wrap; box-sizing: border-box; font-size: 18px; text-align: left; line-height: 1.5;";
			messageContent.innerText = userMessage;

			// Add label and message of the user to the chat area and scroll to the bottom
			chatArea.appendChild(messageContent);
			chatArea.scrollTop = chatArea.scrollHeight;

			// Add dancing dots
			appendChatbotMessage("", chatArea, "waiting");

			// API CALL: GENERATE THE NEXT QUESTION
			jQuery.ajax({
				url: endpoint,
				timeout: 60000,
				type: "POST",
				data: JSON.stringify({
					route: "next",
					payload: {
						user_message: userMessage,
						session_id: userID,
						interview_id: interviewID
					}
				}),
				contentType: "application/json",
				dataType: "json",
				success: function (data) {
					var next_question = data.message.trim();

					// Check if this is the last message of the interview
					var endInterviewIndex = next_question.indexOf("---END---");
					if (endInterviewIndex !== -1) {
						// End of interview
						next_question = next_question.replace("---END---", "");
						next_question = next_question.trim();
						submitButton.disabled = true;
						submitButton.innerText = TEXT.end;
					} else {
						// Interview continues
						submitButton.disabled = false;
						submitButton.innerText = TEXT.submit;
						submitButton.style.backgroundColor = '#007BFF';
					}
					appendChatbotMessage(next_question, chatArea, "response");
				},
				// REQUEST UNSUCCESSFUL
				error: function (jqXHR, textStatus, errorThrown) {
					console.error("Error:", errorThrown);
					appendChatbotMessage(TEXT.errorNext, chatArea, "response");
					submitButton.disabled = false;
					submitButton.style.backgroundColor = '#007BFF';
					submitButton.innerText = TEXT.submit;
				}
			});
		}
	});

});

Qualtrics.SurveyEngine.addOnReady(function () {
	/*Place your JavaScript here to run when the page is fully displayed*/

});

Qualtrics.SurveyEngine.addOnUnload(function () {
	/*Place your JavaScript here to run when the page is unloaded*/

});
