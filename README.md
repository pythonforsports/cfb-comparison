Description:
This Plotly dash app web scrapes from ESPN and USA today to pull schedules, rankings and basic team metrics. 
When ran, this launches a localhost site which allows interaction. The interaction provides team selection and comparison 
to FBS/G5/Conference.

Dependencies:
-Built using Python 3.6.1
-pip install dash  # The core dash backend
-pip install dash-renderer  # The dash front-end
-pip install dash-html-components  # HTML components
-pip install dash-core-components  # Supercharged components
-pip install plotly  # Plotly graphing library used in examples
-pip install pandas #dataframe analyses

Getting Started:
-Move all files to local folder
-Run the app with: $ python app.py
-visit http:127.0.0.1:8050/ in your web browser

Issues/Needs:
-Trouble accessing some teams (e.g. UAB)
-Would like to highlight row of selected team
-Convert SOS table into graph
-

