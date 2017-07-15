import dash
import pandas as pd
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

# Read List of Teams and their football conference
teams = pd.read_csv("collegefootballteams.csv", encoding="ISO-8859-1")
teams_dict = teams.groupby('Conference')['TeamAlt'].apply(list).to_dict()

# Strength of Schedule, FPI and USA Today ranking sites
sos = pd.read_html('http://www.espn.com/college-football/statistics/teamratings/_/sort/sosRemainingRank/order/false',
                   header=1)
fpi = pd.read_html('http://www.espn.com/college-football/statistics/teamratings',
                   header=1)
coaches_ranking = pd.read_html('http://sportspolls.usatoday.com/ncaa/football/polls/coaches-poll/',
                   header=0)
fb_efficiency = pd.read_html('http://www.espn.com/college-football/statistics/teamratings/_/tab/efficiency', header=1)

# ESPN Team Efficiencies
fb_efficiency_df = fb_efficiency[0]
fb_efficiency_df.columns = ['Rk', 'Team', 'Offense', 'Defense', 'Special Teams', 'Overall']
# Split Team column into Team and Conference
fb_efficiency_df[['Team', 'Conference']] = pd.DataFrame([x.split(',') for x in fb_efficiency_df['Team'].tolist()])
pandas_fb_efficiency = pd.DataFrame(fb_efficiency_df, columns=['Rank', 'Team', 'Conference', 'Offense', 'Defense',
                                                               'Special Teams', 'Overall'])
pandas_fb_efficiency = pandas_fb_efficiency[pandas_fb_efficiency.Team != 'TEAM']
pandas_fb_efficiency.reset_index(drop=True, inplace=True)
pandas_fb_efficiency.index = pandas_fb_efficiency.index + 1
pandas_fb_efficiency['Rank'] = pandas_fb_efficiency.index

# Strength of schedule data frame
sos_df = sos[0]
sos_df.columns = ['RK', 'Team', 'W-L', 'Proj W-L', 'WIN OUT%', 'CONF WIN%', 'SOS', 'FPI']
# Split Team column into Team and Conference
sos_df[['Team', 'Conference']] = pd.DataFrame([x.split(',') for x in sos_df['Team'].tolist()])
pandas_sos = pd.DataFrame(sos_df, columns=['Rank', 'Team', 'Conference', 'W-L', 'SOS', 'FPI'])
pandas_sos = pandas_sos[pandas_sos.Team != 'TEAM']
pandas_sos.reset_index(drop=True, inplace=True)
pandas_sos.index = pandas_sos.index + 1
pandas_sos['Rank'] = pandas_sos.index

# CFP & AP Poll Rankings - Merge with alternate team name used by ESPN
cfb_rank = pd.read_html('http://www.espn.com/college-football/playoffPicture', header=1)
cfb_rank_df = cfb_rank[0]
cfb_rank_df = pd.DataFrame(cfb_rank_df, columns=['TEAM', 'CFP', 'AP POLL'])
cfb_rank_df.columns = ['Team', 'CFP', 'AP Poll']
cfb_rank_df = cfb_rank_df[cfb_rank_df.Team != 'NaN']
cfb_rank_df = cfb_rank_df.dropna(how='all')
cfb_rank_df = pd.merge(teams, cfb_rank_df, on='Team')
cfb_rank_df = pd.DataFrame(cfb_rank_df, columns=['Team', 'TeamAlt', 'CFP', 'AP Poll'])

# USA Today Coaches Rankings
coaches_ranking_df = coaches_ranking[0]
coaches_ranking_df.columns = ['Coaches', 'Team', 'Record', 'Points', 'Votes', 'Prev', 'Change', 'Hi/Low']
coaches_ranking_df = pd.DataFrame(coaches_ranking_df, columns=['Team', 'Coaches'])
coaches_ranking_df = pd.merge(coaches_ranking_df, teams, on='Team', how='outer')
coaches_ranking_df = pd.DataFrame(coaches_ranking_df, columns=['Team', 'TeamAlt', 'Coaches'])
coaches_ranking_df = coaches_ranking_df.fillna('--')

# ESPN FPI Ratings
fpi_df = fpi[0]
fpi_df.columns = ['RK', 'Team', 'W-L', 'Proj W-L', 'WIN OUT%', 'CONF WIN%', 'SOS', 'FPI']
# Concatenate FPI ranking with FPI metric
fpi_df['FPI'] = fpi_df['FPI'].map(str) + ' (' + fpi_df['RK'] + ')'
# Split Team column into Team and Conference - Use "TeamAlt" to join back to ESPN's alternate Team name
fpi_df[['TeamAlt', 'Conference']] = pd.DataFrame([x.split(',') for x in fpi_df['Team'].tolist()])
fpi_df = pd.DataFrame(fpi_df, columns=['TeamAlt', 'FPI'])
fpi_df = fpi_df[fpi_df.TeamAlt != 'TEAM']

# Combine coaches ranking with FPI
fpi_coaches_df = pd.merge(coaches_ranking_df, fpi_df, on='TeamAlt', how='outer')
fpi_coaches_df = pd.DataFrame(fpi_coaches_df, columns=['TeamAlt', 'FPI', 'Coaches'])

# Combine coaches ranking and FPI with CFP & AP
rankings_df = pd.merge(cfb_rank_df, fpi_coaches_df, on='TeamAlt', how='outer')
rankings_df = rankings_df.fillna('--')
rankings_df.columns = ['TeamOld', 'Team', 'CFP', 'AP Poll', 'FPI', 'Coaches']
rankings_df = pd.DataFrame(rankings_df, columns=['Team', 'CFP', 'AP Poll', 'Coaches', 'FPI'])

app = dash.Dash()
app.config.supress_callback_exceptions = True


@app.callback(
    dash.dependencies.Output('team_dropdown', 'options'),
    [dash.dependencies.Input('conference_dropdown', 'value')])
def set_team_options(selected_conference):
    return [{'label': i, 'value': i} for i in teams_dict[selected_conference]]


@app.callback(
    dash.dependencies.Output('team_dropdown', 'value'),
    [dash.dependencies.Input('team_dropdown', 'options')])
def set_team_value(available_options):
    return available_options[0]['value']


@app.callback(
    Output(component_id='sos-table', component_property='children'),
    [dash.dependencies.Input(component_id='group-filter', component_property='value'),
     Input(component_id='conference_dropdown', component_property='value'),
     Input(component_id='team_dropdown', component_property='value')]
)
def generate_sos_table(filter, conference, team, max_rows=20):
    filtered_df = []
    if filter == 'conf':
        user_team = pandas_sos[pandas_sos["Team"] == team]
        user_conference = pandas_sos[pandas_sos["Conference"].str.contains(conference, na=False)]
        filtered_df = pd.concat([user_conference, user_team])
        filtered_df.drop_duplicates(subset=['Team'], inplace=True)
        filtered_df.reset_index(drop=True, inplace=True)
        filtered_df.index = filtered_df.index + 1
        filtered_df['Rank'] = filtered_df.index
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'W-L', 'SOS'])

    elif filter == 'FBS':
        user_team = pandas_sos[pandas_sos["Team"] == team]
        top_10_rows = pandas_sos.head(10)
        filtered_df = pd.concat([top_10_rows, user_team])
        filtered_df.drop_duplicates(subset=['Team'], inplace=True)
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'W-L', 'SOS'])
        filtered_df.style.applymap('color: red')

    elif filter == 'G5':
        user_team = pandas_sos[pandas_sos["Team"] == team]
        user_team[['SOS']] = user_team[['SOS']].apply(pd.to_numeric)
        filter_group5_teams = \
            pandas_sos[pandas_sos['Conference'].str.contains("MW|American|Sun Belt|MAC|C-USA", na=False)]
        filter_group5_teams[['SOS']] = filter_group5_teams[['SOS']].apply(pd.to_numeric)
        df = pd.concat([user_team, filter_group5_teams])
        df.drop_duplicates(subset=['Team'], inplace=True)
        first_df = df.sort_values(by='SOS')
        first_df.reset_index(drop=True, inplace=True)
        first_df.index = first_df.index + 1
        first_df['Rank'] = first_df.index
        top_10_rows = first_df.head(10)
        user_team2 = first_df[first_df["Team"] == team]
        second_df = top_10_rows.sort_values(by='SOS')
        second_df.reset_index(drop=True, inplace=True)
        second_df.index = second_df.index + 1
        second_df['Rank'] = second_df.index
        filtered_df = pd.concat([second_df, user_team2])
        filtered_df.drop_duplicates(subset=['Team', 'Rank'], inplace=True)
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'W-L', 'SOS'])

    return html.Table(
        # Header1
        [html.Tr([
            html.Th(html.H6([team + ' ' + 'Strength of Schedule' + ' (vs. ' + filter + ')']),
                    colSpan=5, style=dict(textAlign="center")),
        ])] +

        # Header2
        [html.Tr([html.Td(col) for col in filtered_df.columns], style=dict(fontWeight="bold"))] +

        # Body
        [html.Tr([
            html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns
        ]) for i in range(min(len(filtered_df), max_rows))]
    )


@app.callback(
    Output(component_id='sched-table', component_property='children'),
    [Input(component_id='team_dropdown', component_property='value'),
     dash.dependencies.Input(component_id='year-slider', component_property='value')]
)
def generate_sched_table(team, year, max_rows=20):
    df = pd.DataFrame(teams)
    filter_team = df.loc[df["TeamAlt"] == team]
    filter_team['ESPNID'] = "http://www.espn.com/college-football/team/fpi/_/id/" \
                            + filter_team.ESPNID.map(str) + "/year/" + str(year)
    link = filter_team.tail(1)['ESPNID'].values[0]
    sched_dataframe = pd.read_html(link, header=1)[4]
    sched_dataframe.columns = ['Date', 'Opponent', 'Result/Proj', 'Opp FPI', 'Game Rating']

    return html.Table(
        # Header1
        [html.Tr([
            html.Th(html.H6([team + ' ' + str(year) + ' ' + 'Schedule']), colSpan=5, style=dict(textAlign="center")),
        ])] +

        # Header2
        [html.Tr([html.Td(col) for col in sched_dataframe.columns], style=dict(fontWeight="bold"))] +

        # Body
        [html.Tr([
            html.Td(sched_dataframe.iloc[i][col]) for col in sched_dataframe.columns
        ]) for i in range(min(len(sched_dataframe), max_rows))]
    )


@app.callback(
    Output(component_id='stats-table', component_property='children'),
    [dash.dependencies.Input(component_id='group-filter', component_property='value'),
     Input(component_id='conference_dropdown', component_property='value'),
     Input(component_id='team_dropdown', component_property='value')]
)
def generate_stats_table(groupfilter, conference, team, max_rows=20):
    filtered_df = []
    if groupfilter == 'conf':
        user_team = pandas_fb_efficiency[pandas_fb_efficiency["Team"] == team]
        user_conference = pandas_fb_efficiency[pandas_fb_efficiency["Conference"].str.contains(conference, na=False)]
        filtered_df = pd.concat([user_conference, user_team])
        filtered_df.drop_duplicates(subset=['Team'], inplace=True)
        filtered_df.reset_index(drop=True, inplace=True)
        filtered_df.index = filtered_df.index + 1
        filtered_df['Rank'] = filtered_df.index
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'Offense', 'Defense',
                                                         'Special Teams', 'Overall'])

    elif groupfilter == 'FBS':
        user_team = pandas_fb_efficiency[pandas_fb_efficiency["Team"] == team]
        top_10_rows = pandas_fb_efficiency.head(10)
        filtered_df = pd.concat([top_10_rows, user_team])
        filtered_df.drop_duplicates(subset=['Team'], inplace=True)
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'Offense', 'Defense',
                                                         'Special Teams', 'Overall'])

    elif groupfilter == 'G5':
        user_team = pandas_fb_efficiency[pandas_fb_efficiency["Team"] == team]
        filter_group5_teams = \
            pandas_fb_efficiency[pandas_fb_efficiency['Conference'].str.contains("MW|American|Sun Belt|MAC|C-USA",
                                                                                 na=False)]
        df = pd.concat([user_team, filter_group5_teams])
        df.drop_duplicates(subset=['Team'], inplace=True)
        first_df = df.sort_values(by='Overall', ascending=False)
        first_df.reset_index(drop=True, inplace=True)
        first_df.index = first_df.index + 1
        first_df['Rank'] = first_df.index
        top_10_rows = first_df.head(10)
        user_team2 = first_df[first_df["Team"] == team]
        second_df = top_10_rows.sort_values(by='Overall', ascending=False)
        second_df.reset_index(drop=True, inplace=True)
        second_df.index = second_df.index + 1
        second_df['Rank'] = second_df.index
        filtered_df = pd.concat([second_df, user_team2])
        filtered_df.drop_duplicates(subset=['Team'], inplace=True)
        filtered_df = pd.DataFrame(filtered_df, columns=['Rank', 'Team', 'Conference', 'Offense', 'Defense',
                                                         'Special Teams', 'Overall'])

    return html.Table(
        # Header1
        [html.Tr([
            html.Th(html.H6([team + ' ' + 'Team Efficiency' + ' (vs. ' + groupfilter + ')']), colSpan=7,
                    style=dict(textAlign="center", background="#42444e", color="#fff")),
        ])] +

        # Header2
        [html.Tr([html.Td(col) for col in filtered_df.columns], style=dict(fontWeight="bold"))] +

        # Body
        [html.Tr([
            html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns
        ]) for i in range(min(len(filtered_df), max_rows))]
    )


@app.callback(
    Output(component_id='ranking-table', component_property='children'),
    [dash.dependencies.Input(component_id='team_dropdown', component_property='value')]
)
def fetch_cfp_rank(team, max_rows=2):
    user_team = rankings_df[rankings_df.Team == team]
    user_team = pd.DataFrame(user_team, columns=['CFP', 'AP Poll', 'Coaches', 'FPI'])

    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in user_team.columns])] +

        # Body
        [html.Tr([
            html.Td(user_team.iloc[i][col]) for col in user_team.columns
        ]) for i in range(min(len(user_team), max_rows))]
    )


app.layout = html.Div([

    html.Div([
        dcc.Slider(
            id='year-slider',
            min=2010,
            max=2018,
            marks={i: '{}'.format(i) if i == 2010 else str(i) for i in range(2010, 2018)},
            value=2017
        ),
    ], style={'width': '20%', 'marginTop': '140',
              'marginLeft': '275', 'float': 'left', 'display': 'inline-block', }),

    html.Div([
        html.Label('Conference'),
        dcc.Dropdown(
            id='conference_dropdown',
            options=[{'label': k, 'value': k} for k in teams_dict.keys()],
        ),

    ], style={'width': '10%',
              'display': 'inline-block',
              'float': 'left',
              'marginTop': '15',
              'marginBottom': '120'

              }),

    html.Div([
        html.Label('Team'),
        dcc.Dropdown(
            id='team_dropdown'
        ),
    ], style={'width': '10%',
              'float': 'center',
              'display': 'inline-block',
              'marginTop': '15',
              'marginLeft': '5',
              'marginBottom': '120'
              }),

    html.Div([
        html.Label('Filter to'),
        dcc.Dropdown(
            id='group-filter',
            options=[
                {'label': 'FBS', 'value': 'FBS'},
                {'label': 'Group of 5', 'value': 'G5'},
                {'label': 'Conference', 'value': 'conf'}],
            value='conf',
        )], style={'width': '7%',
                   'marginBottom': '120',
                   'float': 'center',
                   'display': 'inline-block',
                   'marginLeft': '5',
                   'marginTop': '15'
                   }),

    html.Div(id='ranking-table', style={'float': 'right', 'marginTop': '28', 'marginRight': '375'}),

    html.Div([
        html.Div([
            html.Div(id='sched-table', style={'marginLeft': '230', 'float': 'left'}),
            html.Div(id='sos-table', style={'marginLeft': '25', 'float': 'left'}),
            html.Div(id='stats-table', style={'marginLeft': '25', 'float': 'left'}),
        ], style={}),

    ], style={'display': 'inline', 'columnCount': 2}),

    app.css.append_css({
        'external_url': (
            # 'https://codepen.io/scottj84/pen/WOgqGO.css'
            'https://codepen.io/scottj84/pen/XgPvRJ.css'
        )
    })
])

if __name__ == '__main__':
    app.run_server()
