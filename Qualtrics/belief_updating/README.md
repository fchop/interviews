# Qualtrics integration for the belief-updating study

Files used in the "AI Interview Testing" block of the Qualtrics survey *Beliefs Full - German v2.1*
(`SV_9Sx5yCLlJ2Igiiy`). They are adapted from `../without_voice`.

## Survey flow: embedded data

An **Embedded Data** element early in the survey flow (after the "Group: Data" wheel settings) holds:

| Field | Value | Purpose |
|---|---|---|
| `user_id` | `${e://Field/ResponseID}` | session id sent to the interview API; equals the Qualtrics ResponseID so transcripts can be merged with survey data |
| `interview_endpoint` | `https://595d5bhbu0.execute-api.eu-central-1.amazonaws.com/Prod/` | the deployed Lambda API |
| `interview_id` | *(empty)* | which interview configuration is used; set by the interviewer-selection question |
| `first_question` | *(empty)* | filled by the interview question with the opening question text |

## Question 1: interviewer selection (multiple choice, single answer)

Choices, in this order (the JavaScript maps choice position to configuration; the labels are the keys):

1. `Qual_Interview_4.1_age_8` — 8-year-olds, English
2. `Qual_Interview_4.1_age_8_DE` — 8-year-olds, German
3. `Qual_Interview_4.2` — adults, English
4. `Qual_Interview_4.2_DE` — adults, German

Paste `select_interviewer.js` into this question's JavaScript. It writes the matching configuration key to
the embedded data field `interview_id` when the page is submitted. **A page break must follow this question**
so that the value is set before the interview question loads.

## Question 2: the interview (Text / Graphic)

- Paste `interview.html` into the question's HTML view.
- Paste `interview.js` into the question's JavaScript.

`interview.js` is `../without_voice/Qualtrics.js` plus: German button/placeholder texts when the selected
configuration ends in `_DE`, and a visible setup error in the chat area if the embedded data is missing.
