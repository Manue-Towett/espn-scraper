import json

with open("data.json", "r") as file:
    data = json.load(file)

with open("schedule.json", "w") as file:
    team_schedule = data["page"]["content"]["scheduleData"]["teamSchedule"]

    json.dump(team_schedule, file, indent=4)

with open("posts.json", "w") as file:
    posts = team_schedule[0]["events"]["post"][0]["group"]

    json.dump(posts, file, indent=4)

with open("leagues.json", "w") as file:
    leagues = data["page"]["content"]["teams"]

    json.dump(leagues, file, indent=4)


with open("seasons.json", "w") as file:
    seasons = data["page"]["content"]["scheduleData"]["seasons"]

    json.dump(seasons, file, indent=4)