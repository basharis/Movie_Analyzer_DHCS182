import json
import datetime
import os
import math
import ntpath
import operator
from imdb import IMDb
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import *


stop_words = stopwords.words('english')
swear_words = []
sat_words = []
with open("swear_words.txt", "r", encoding="ascii", errors='ignore') as f:
    f = f.read()
    for line in f.split('\n'):
        swear_words.append(line)
with open("sat_words.txt", "r", encoding="ascii", errors='ignore') as f:
    f = f.read()
    for line in f.split('\n'):
        sat_words.append(line)


class SubAnalyzer(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.stop_words = stop_words
        self.sat_words = sat_words
        self.swear_words = swear_words
        self.raw_bag_of_words = self.subtitle_to_bag_of_words(False)
        self.bag_of_words = self.subtitle_to_bag_of_words(True)

        self.mv_name = ntpath.basename(self.file_path)
        self.mv_name = os.path.splitext(self.mv_name)[0]

    def english_letter(self, l):
        return (l >= 'a' and l <= 'z') or (l >= 'A' and l <= 'Z')

    def subtitle_to_bag_of_words(self, stopwords_flag=True):
        tk = RegexpTokenizer(r'\w+')
        st = WordNetLemmatizer()
        bag_of_words = []
        with open(self.file_path, "r", encoding="ascii", errors='ignore') as f:
            f = f.read()
            for line in f.split('\n'):
                for word in line.split(' '):
                    if word != '' and self.english_letter(word[0]):
                        word = tk.tokenize(word)                                # trim punctuation
                        word = st.lemmatize(word[0])                            # lemmatize the word   --- CALC HEAVY OPERATION
                        word = word.lower()                                     # convert to lower case
                        if stopwords_flag and word not in self.stop_words:      # make sure it is not a stopword
                            bag_of_words.append(word)
                        elif not stopwords_flag:
                            bag_of_words.append(word)
        return bag_of_words

    def common_words(self):
        counts = dict()
        for word in self.bag_of_words:
                if word in counts.keys():
                    counts[word] = counts[word] + 1
                else:
                    counts[word] = 1
        counts = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        return counts

    def num_of_words(self, raw=True):
        return len(self.raw_bag_of_words) if raw else len(self.bag_of_words)

    def movie_length(self):
        # Extract runtime information from IMDb
        ia = IMDb()
        s_result = ia.search_movie(self.mv_name)                 # CALC HEAVY OPERATION
        s_result = s_result[0]
        ia.update(s_result)
        if 'runtimes' in s_result.keys():
            length = int(s_result['runtimes'][0])
        else:
            length = 110
        return length

    def words_per_minute(self):
        return int(self.num_of_words() / self.movie_length())

    def meter_score(self, meter_type):
        i = 0
        words_list = []
        if meter_type == 'sat':
            words_list = self.sat_words
        elif meter_type == 'swear':
            words_list = self.swear_words
        else:
            print("ERROR: not a valid meter")
        for word in self.bag_of_words:
            if word in words_list:
                i = i+1
        return i / self.num_of_words()



#############   Similarity

analyzers = []

def set_globals():
    global num_docs_contain_word
    num_docs_contain_word = dict()
    global analyzers
    global corpus_size
    corpus_size = len(os.listdir("corpus"))
    global avg_num_words
    avg_num_words = average_num_of_words()


def create_analyzers():
    print("Creating subtitles analyzers for the entire corpus...")
    for name in os.listdir("corpus"):
        other_analyzer = SubAnalyzer(os.path.join("corpus", name))
        analyzers.append((name, other_analyzer))


def average_num_of_words():
    i = 0
    for analyzer in analyzers:
        analyzer = analyzer[1]
        i += analyzer.num_of_words()
    return i / corpus_size


def fill_dfw_values(analyzer):
    print("Creating df(w) values")
    word_dict = {}
    bag_of_words = analyzer.bag_of_words
    for other_analyzer in analyzers:
        name = other_analyzer[0]
        other_analyzer = other_analyzer[1]
        other_bag_of_words = other_analyzer.bag_of_words
        for word in bag_of_words:
            if not word_dict.get(word, []):
                word_dict[word] = []
            if name in word_dict[word]:
                continue
            for word_ins in other_bag_of_words:
                if word == word_ins:
                    word_dict[word].append(name)
                    if word not in num_docs_contain_word.keys():
                        num_docs_contain_word[word] = 1
                    else:
                        num_docs_contain_word[word] += 1
                    break


def df(word):
    return num_docs_contain_word[word]


def tf(analyzer, word):
    global avg_num_words
    count_occ = 0
    k = 1.6
    b = 0.75
    length = analyzer.num_of_words()
    for word_ins in analyzer.bag_of_words:
        if word == word_ins:
            count_occ += 1
    result = (count_occ * (k+1)) / (count_occ + k * (1 - b + b * (length / avg_num_words)))
    return result


def idf(word):
    return math.log((corpus_size + 1) / df(word))


def bm25(analyzer1, analyzer2):
    score = 0
    bag_of_words = analyzer1.bag_of_words
    for word in bag_of_words:
        score += tf(analyzer1, word) * tf(analyzer2, word) * idf(word)
    return score


def similar_movies(analyzer):
    global num_docs_contain_word
    num_docs_contain_word = dict()
    print("### Working on:  " + analyzer.file_path)
    fill_dfw_values(analyzer)
    movie_scores = []
    for other_analyzer in analyzers:
        name = other_analyzer[0]
        other_analyzer = other_analyzer[1]
        print("Checking similarity with: " + other_analyzer.file_path)
        movie_scores.append((bm25(analyzer, other_analyzer), os.path.splitext(name)[0]))
    return sorted(movie_scores, reverse=True)


def update_similar_for(mv_name):
    print("Creating list of movies similar to " + mv_name + "...")
    create_analyzers()
    set_globals()
    file_path = os.path.join("corpus", mv_name + ".srt")
    analyzer = SubAnalyzer(file_path)
    similar = similar_movies(analyzer)
    with open(os.path.join("similar", analyzer.mv_name + ".txt"), "w") as f:
        for rec in similar:
            f.write("%f %s\n" % (rec[0], rec[1]))


def update_similar_lists():  # VERY SLOW - USE WITH CAUTION
    print("Creating similar movies lists...")
    create_analyzers()
    set_globals()
    for analyzer in analyzers:
        name = analyzer[0]
        analyzer = analyzer[1]
        similar = similar_movies(analyzer)
        with open(os.path.join("similar", os.path.splitext(name)[0] + ".txt"), "w") as f:
            for rec in similar:
                f.write("%f %s\n" % (rec[0], rec[1]))
    # Update stats
    with open("metadata.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data['latest_update_lists']['similar'] = str(datetime.datetime.now())
    with open("metadata.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)
    # End Update


def main():
    # update_top_lists()
    # update_similar_lists()
    print("BYE!")


if __name__ == "__main__":
    main()