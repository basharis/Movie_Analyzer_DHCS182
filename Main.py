import os
import json
import datetime
import shlex
import SubAnalyzer
from imdb import IMDb
from OSDownloader import OpenSub


EXIT_SUCCESS = 0
EXIT_FAILURE = -1
JSON_DEST_PATH = 'json'
downloader = OpenSub("corpus")
query_types = ['dirty', 'vocal', 'complex']
rev_query_types = ['clean', 'quiet', 'easy']
imdb_api = IMDb()
funcs = {}
update_types = {}


def set_global_variables():
    global EXIT_FAILURE
    global EXIT_SUCCESS
    global JSON_DEST_PATH
    global downloader
    global query_types
    global rev_query_types
    global imdb_api
    global funcs
    funcs['mvinfo'] = movie_info
    funcs['cmp'] = compare
    funcs['top'] = top
    funcs['similar'] = similar
    funcs['update'] = update
    funcs['stats'] = stats
    funcs['help'] = help
    funcs['quit'] = quit
    global update_types
    update_types['top_lists'] = update_top_lists
    update_types['similar_lists'] = SubAnalyzer.update_similar_lists
    update_types['movie_info'] = update_movies_info
    update_types['avg'] = update_averages


def fill_info(mv_name, sub_file_path):
    json_result = {}
    s_result = imdb_api.search_movie(mv_name)
    s_result = s_result[0]
    imdb_api.update(s_result)
    try:
        json_result['title'] = s_result['title']
        json_result['year'] = s_result['year']
        json_result['genres'] = s_result['genres']
        json_result['runtime'] = s_result['runtime']
        json_result['rating'] = s_result['rating']
        json_result['plot'] = s_result['plot']
        langs = s_result['languages']
    except KeyError:
        json_result['genres'] = 'None'
        json_result['runtime'] = 110
        json_result['rating'] = 'NR'
        json_result['plot'] = 'None'
        langs = 'None'
    analyzer = SubAnalyzer.SubAnalyzer(sub_file_path)
    dirty_score = analyzer.meter_score('swear') * 100
    sat_score = analyzer.meter_score('sat') * 100
    wpm = analyzer.words_per_minute()
    common_words = analyzer.common_words()[:10]
    common_words_dict = dict()
    for rec in common_words:
        common_words_dict[rec[0]] = rec[1]
    json_result['language'] = {'id': langs,
                               'adult_language_percentage': dirty_score,
                               'linguistic_difficulty_percentage': sat_score,
                               'words_per_minute': wpm,
                               'common_words': common_words_dict}
    return json_result


def movie_info(cmd, override=False):
    if len(cmd) == 2:
        mv_name = cmd[1]
    else:
        print("Invalid number of arguments - type \'help\' for assistance")
        return
    json_file_path = os.path.join(JSON_DEST_PATH, 'movies', mv_name.capitalize() + '.json')
    sub_file_path = downloader.search_and_download(mv_name)
    if not override and os.path.isfile(json_file_path):
        print('JSON file exists: ' + json_file_path)
        return
    print("Creating JSON file for " + mv_name + "...")
    json_result = fill_info(mv_name, sub_file_path)
    json_file_path = os.path.join(JSON_DEST_PATH, 'movies', json_result['title'] + '.json')
    with open(json_file_path, 'w') as tf:
        json.dump(json_result, tf, indent=4)
    print("JSON file created: " + json_file_path)


def update_movies_info():
    files = os.listdir("corpus")
    for file in files:
        mv_name = os.path.splitext(file)[0]
        movie_info(['mvinfo', mv_name], True)
    # Update stats
    with open("metadata.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data['num_of_movies_in_db'] = len(files)
    data['latest_update_lists']['movie_info'] = str(datetime.datetime.now())
    with open("metadata.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)


def update_averages():
    print("Updating averages in metadata.json...")
    avg_swear = 0
    avg_sat = 0
    avg_wpm = 0
    mv_json_path = os.path.join('json', 'movies')
    json_files = os.listdir(mv_json_path)
    num_of_movies = len(json_files)
    json_files = (json_file for json_file in json_files if str(json_file)[-4:] == 'json')
    for mv_json in json_files:
        with open(os.path.join(mv_json_path, mv_json), 'r') as tf:
            mv_data = json.load(tf)
            avg_swear += mv_data['language']['adult_language_percentage']
            avg_sat += mv_data['language']['linguistic_difficulty_percentage']
            avg_wpm += mv_data['language']['words_per_minute']
    avg_swear = avg_swear / num_of_movies
    avg_sat = avg_sat / num_of_movies
    avg_wpm = avg_wpm / num_of_movies
    # Update stats
    with open("metadata.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data['latest_update_lists']['avg'] = str(datetime.datetime.now())
    data['avg_score']['dirty_lang'] = avg_swear
    data['avg_score']['complex_lang'] = avg_sat
    data['avg_score']['words_per_minute'] = avg_wpm
    with open("metadata.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)


def update_top_lists():
    print("Updating top lists in metadata.json...")
    top_sat = []
    top_swear = []
    top_wpm = []
    mv_json_path = os.path.join('json', 'movies')
    json_files = os.listdir(mv_json_path)
    json_files = (json_file for json_file in json_files if str(json_file)[-4:] == 'json')
    for mv_json in json_files:
        with open(os.path.join(mv_json_path, mv_json), 'r') as tf:
            mv_name = os.path.splitext(mv_json)[0]
            mv_data = json.load(tf)
            top_swear.append((mv_data['language']['adult_language_percentage'], mv_name))
            top_sat.append((mv_data['language']['linguistic_difficulty_percentage'], mv_name))
            top_wpm.append((mv_data['language']['words_per_minute'], mv_name))
    top_sat = sorted(top_sat, reverse=True)
    top_swear = sorted(top_swear, reverse=True)
    top_wpm = sorted(top_wpm, reverse=True)
    with open(os.path.join("top", "complex.txt"), "w") as f:
        for mv in top_sat:
            f.write("%f %s\n" % (mv[0], mv[1]))
    with open(os.path.join("top", "dirty.txt"), "w") as f:
        for mv in top_swear:
            f.write("%f %s\n" % (mv[0], mv[1]))
    with open(os.path.join("top", "vocal.txt"), "w") as f:
        for mv in top_wpm:
            f.write("%d %s\n" % (mv[0], mv[1]))
    # Update stats
    with open("metadata.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data['latest_update_lists']['top'] = str(datetime.datetime.now())
    with open("metadata.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)
    # End Update


def compare(cmd):
    if len(cmd) == 3:
        mv_name1 = cmd[1]
        mv_name2 = cmd[2]
    else:
        print("Invalid number of arguments - type \'help\' for assistance")
        return
    json_file_path_op1 = os.path.join(JSON_DEST_PATH, 'comparisons', mv_name1.capitalize() + " x " + mv_name2.capitalize() + '.json')
    json_file_path_op2 = os.path.join(JSON_DEST_PATH, 'comparisons', mv_name2.capitalize() + " x " + mv_name1.capitalize() + '.json')
    if os.path.isfile(json_file_path_op1):
        print('JSON file exists: ' + json_file_path_op1)
        return
    elif os.path.isfile(json_file_path_op2):
        print('JSON file exists: ' + json_file_path_op2)
        return
    sub_file_path1 = downloader.search_and_download(mv_name1)
    sub_file_path2 = downloader.search_and_download(mv_name2)
    json_result = [fill_info(mv_name1, sub_file_path1), fill_info(mv_name2, sub_file_path2)]
    json_file_path = os.path.join(JSON_DEST_PATH, 'comparisons', json_result[0]['title'] + " x " + json_result[1]['title'] + '.json')
    with open(json_file_path, 'w') as tf:
        json.dump(json_result, tf, indent=4)
    print("JSON file created: " + json_file_path)


def top(cmd):
    if len(cmd) == 3:
        num = int(cmd[1])
        query_type = cmd[2]
    else:
        print("Invalid number of arguments - type \'help\' for assistance")
        return
    if query_type in query_types:
        filename = os.path.join("top", query_type + ".txt")
        with open(filename, 'r') as f:
            f = f.read()
            top_results = f.split('\n')
            top_results = top_results[:num]
    elif query_type in rev_query_types:
        filename = os.path.join("top", query_types[rev_query_types.index(query_type)] + ".txt")
        with open(filename, 'r') as f:
            f = f.read()
            top_results = f.split('\n')
            top_results = top_results[(num+1)*(-1):]
            top_results.pop()
            top_results = list(reversed(top_results))
    else:
        print("Invalid query - type \'help\' for assistance")
        return
    json_result = []
    i = 1
    for result in top_results:
        score = result.split(' ', 1)[0]
        mv_name = result.split(' ', 1)[1]
        rank = i
        json_result.append({'rank': rank, 'title': mv_name, 'score': float(score)})
        i += 1
    json_file_path = os.path.join(JSON_DEST_PATH, 'top', "top_" + str(num) + "_" + query_type + ".json")
    with open(json_file_path, 'w') as tf:
        json.dump(json_result, tf, indent=4)
    print("JSON file created: " + json_file_path)


def similar(cmd):
    if len(cmd) == 3:
        num = int(cmd[1])
        mv_name = cmd[2]
    else:
        print("Invalid number of arguments - type \'help\' for assistance")
        return
    try:
        with open(os.path.join("similar", mv_name + ".txt"), "r") as f:
            f = f.read()
            i = 0
            json_result = []
            for mv in f.split("\n"):
                if i == 0:  # Skip first one - same movie
                    i += 1
                    continue
                score = mv.split(' ', 1)[0]
                name = mv.split(' ', 1)[1]
                rank = i
                json_result.append({'rank': rank, 'title': name, 'score': float(score)})
                i += 1
                if i > num:
                    break
        json_file_path = os.path.join(JSON_DEST_PATH, 'similar', "similar_" + str(num) + "_" + mv_name + ".json")
        with open(json_file_path, 'w') as tf:
            json.dump(json_result, tf, indent=4)
        print("JSON file created: " + json_file_path)
    except FileNotFoundError:
        SubAnalyzer.update_similar_for(mv_name)
        similar(cmd)


def update(cmd):
    if len(cmd) == 2:
        update_type = cmd[1]
    else:
        print("Invalid number of arguments - type \'help\' for assistance")
        return
    try:
        update_types[update_type]()
    except KeyError:
        print("Invalid update type - type \'help\' for assistance")


def stats(cmd):
    print("Parsing metadata...")
    json_file_path = 'metadata.json'
    with open(json_file_path, 'r') as tf:
        json_parsed = json.load(tf)
        print("""
        Authors: {}
        Number of Movies in DB: {}
        Latest Movie Added:
            Name:               {}
            Time:               {}
        Latest Lists Update:
            Top:                {}
            Similar:            {}
            Movie Info:         {}
            Averages:           {}
        Corpus Average Scores:
            Dirty Language:     {}%
            Complex Language:   {}%
            Words Per Minute:   {}
        """.format(
            json_parsed['authors'],
            json_parsed['num_of_movies_in_db'],
            json_parsed['latest_movie_added']['name'],
            json_parsed['latest_movie_added']['time'],
            json_parsed['latest_update_lists']['top'],
            json_parsed['latest_update_lists']['similar'],
            json_parsed['latest_update_lists']['movie_info'],
            json_parsed['latest_update_lists']['avg'],
            json_parsed['avg_score']['dirty_lang'],
            json_parsed['avg_score']['complex_lang'],
            json_parsed['avg_score']['words_per_minute'])
        )


def help(cmd):
    print(
        """
        mvinfo      MOVIE_NAME                      --- full info for MOVIE_NAME
        cmp         MOVIE_1         MOVIE_2         --- a comparison between MOVIE_1 and MOVIE_2
        top         NUM             QUERY_TYPE      --- top NUM movies that with the highest QUERY_TYPE
        similar     NUM             MOVIE_NAME      --- the NUM most similar movies to MOVIE_NAME
        update                      UPDATE_TYPE     --- updates the stats to include the latest additions to the db
        stats                                       --- program metadata
        help                                        --- brings out this message
        quit                                        --- exit the program
        
        QUERY_TYPE:
            dirty           -- dirty language
            clean           -- clean language
            vocal           -- many words per minute
            quiet           -- less words per minute
            complex         -- high lingual complexity
            easy            -- low lingual complexity
        
        UPDATE_TYPE:
            top_lists       -- update top lists to include newly added movies
            similar_lists   -- update similar lists to include newly added movies
            movie_info      -- update language info to include newly added movies
            avg             -- update avg lang percentages to include newly added movies
        """)


def quit(cmd):
    print("Quitting...")
    exit(EXIT_SUCCESS)


def main():
    set_global_variables()
    while 1:
        print("<MovieAnalyzer@dhcs182>", end=' ')
        cmd = input('')
        if cmd == '':
            continue
        cmd = shlex.split(cmd)
        if cmd[0] == '':
            continue
        try:
            funcs[cmd[0]](cmd)
        except KeyError:
            print("Unknown command - type \'help\' for command list.")


if __name__ == "__main__":
    main()
