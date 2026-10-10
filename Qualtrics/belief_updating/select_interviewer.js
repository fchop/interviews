Qualtrics.SurveyEngine.addOnload(function () {
	/*Place your JavaScript here to run when the page loads*/
});

Qualtrics.SurveyEngine.addOnReady(function () {
	/*Place your JavaScript here to run when the page is fully displayed*/
});

Qualtrics.SurveyEngine.addOnPageSubmit(function (type) {
	// Map the selected choice (by position, 1-based) to an interview configuration key
	// from app/parameters.py and store it in the embedded data field `interview_id`,
	// which the interview question on the next page reads.
	// The choice labels in Qualtrics carry the same keys, in this order.
	var CONFIG_BY_CHOICE = {
		1: "Qual_Interview_4.1_age_8",     // 8-year-olds, English
		2: "Qual_Interview_4.1_age_8_DE",  // 8-year-olds, German
		3: "Qual_Interview_4.2",           // adults, English
		4: "Qual_Interview_4.2_DE"         // adults, German
	};
	var selected = this.getSelectedChoices();
	if (selected.length > 0) {
		var interviewID = CONFIG_BY_CHOICE[selected[0]] || "Qual_Interview_4.1";
		Qualtrics.SurveyEngine.setEmbeddedData("interview_id", interviewID);
	}
});

Qualtrics.SurveyEngine.addOnUnload(function () {
	/*Place your JavaScript here to run when the page is unloaded*/
});
