
REM Activate the virtual environment
call ..\interviews-env\Scripts\activate

REM Open the browser

start http://127.0.0.1:8000/Social_Assistance/test

REM Run the Flask app
python app\app.py

pause

