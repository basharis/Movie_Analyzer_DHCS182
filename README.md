# Movie Script Analyzer - Digital Humanities 2018, Ben Gurion

This is our final project for Digital Humanities for Computer Science class of 2018 in BGU.
The program analyzes movie language through its script and builds JSON outputs.

## Usage:

```
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
```

## Setup:

* Download Python 3.6
* Python modules nltk and IMDbPY, which can be obtained the following way:
```
sudo apt-get update
sudo apt install pip --fix-missing
python -m pip instal --upgrade pip
python -m pip install IMDbPY
python -m pip install nltk

python _modules\install_nltk.py
```

## Authors:

Shahar Bashari, Tamir Eyal

## Disclaimer:
We do not own any of the movies used as source material here.
The scripts are obtained through OpenSubtitles API and used for educational purposes only.
