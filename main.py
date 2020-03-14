# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_render_template]

import sys
import aiohttp
import asyncio
from fpl import FPL
import re
import unicodedata
from flask import Flask, render_template, request

app = Flask(__name__)

player_name_replacement_map = {
    'pereira': 'Barbosa Pereira',
    'taa': 'Alexander-Arnold'
}


@app.route('/')
def root():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def root_post():
    errors = []
    results = []
    score_map = {}
    if request.method == "POST":
        try:
            gw = request.form['game_week']
            team = request.form['team']
        except:
            errors.append(
                "Unable to get gw and team data. Please make sure it's valid and try again."
            )
            return render_template('index.html', errors=errors)
        try:
            if gw and team:
                # text processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                score_map = dict(asyncio.run(get_scores(gw, team)))
        except:
            errors.append(
                "Request failed. Please contact admin"
            )

        return render_template('index.html', errors=errors, results=score_map)


async def get_scores(gameweek, team):
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        teams = await fpl.get_teams()
        team_dict = {i.short_name: i.code for i in teams}
        players = await fpl.get_players(None, True)

        lines = team.splitlines()
        score_map = {}
        for line in lines:
            p = re.split(' +', line)
            player_last_name = p[0]
            if player_last_name.lower() in player_name_replacement_map:
                player_last_name = player_name_replacement_map[player_last_name.lower()]
            team_code = p[1].replace("(", "").replace(")", "").replace("\n", "")

            player_details = get_player_details(player_last_name, team_code, players, team_dict)
            score = get_gameweek_score(player_details, gameweek)
            if len(p) > 2:
                captain = p[2].replace("(", "").replace(")", "").replace("\n", "")
                if captain == 'c':
                    score = score * 2
                    player_last_name = player_last_name + " (c)"

            score_map[player_last_name] = score

        total_score = 0
        for i in score_map:
            total_score = total_score + score_map[i]
        score_map["Total"] = total_score
        return score_map


def get_player_details(last_name, team_abbrev, players, team_dict):
    for player in players:
        normal_name = unicodedata.normalize('NFKD', player.second_name.lower()).encode('ASCII', 'ignore')
        if normal_name.decode("utf-8") == last_name.lower() and player.team_code == team_dict[team_abbrev]:
            return player
    print("Player with name: %s not found " % last_name)


def get_gameweek_score(player, gameweek):
    for history in player.history:
        if history["round"] == int(gameweek):
            return history["total_points"]
    return 0


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [START gae_python37_render_template]
