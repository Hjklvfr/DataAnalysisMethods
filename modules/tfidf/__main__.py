import math
import string
from os import mkdir


from modules.tfidf import GeniusClient, morph


def normalize_text(text):
    # Удаление знаков препинания и приведение к нижнему регистру
    text = text.lower()
    # Разделение строки на слова
    words = text.split()
    words = [word.strip(string.punctuation) for word in words]

    words = list(filter(lambda x: x, words))
    # Лемматизация каждого слова
    lemmas = [morph.parse(word)[0].normal_form for word in words]
    # Объединение лемм обратно в строку
    return ' '.join(lemmas)


def compute_tf(tokenized_docs, vocabulary):
    """
    Computes term frequency for each document.
    Returns a list of dictionaries, one per document.
    """
    tf_list = []
    for tokens in tokenized_docs:
        tf_dict = {}
        total_terms = len(tokens)
        for term in vocabulary:
            tf_dict[term] = tokens.count(term) / total_terms
        tf_list.append(tf_dict)
    return tf_list


def compute_idf(tokenized_docs, vocabulary):
    """
    Computes inverse document frequency for each term in the vocabulary.
    """
    N = len(tokenized_docs)
    idf_dict = {}
    for term in vocabulary:
        # Count the number of documents that contain the term
        df = sum(1 for doc in tokenized_docs if term in doc)
        # Compute IDF with smoothing to avoid division by zero
        idf = math.log((N + 1) / (df + 1)) + 1
        idf_dict[term] = idf
    return idf_dict


def compute_tfidf(tf_list, idf_dict, vocabulary):
    """
    Computes TF-IDF for each term in each document.
    Returns a list of dictionaries, one per document.
    """
    tfidf_list = []
    for tf_dict in tf_list:
        tfidf_dict = {}
        for term in vocabulary:
            tfidf_dict[term] = tf_dict[term] * idf_dict[term]
        tfidf_list.append(tfidf_dict)
    return tfidf_list


def tokenize(document):
    """
    Simple tokenizer that splits on whitespace and converts to lowercase.
    """
    return document.lower().split()

if __name__ == "__main__":
    music_artist = ['20222']
    songs=[]
    g = GeniusClient(music_artist)
    documents=[]
    for artist in music_artist:
        song_list=g.song_list(artist)
        for song in song_list:
            lyrics=g.get_lyrics(song)
            if lyrics:
                documents.append(lyrics.rstrip().strip())
                print(song)
                # with open('C:\\lab3TF-IDF\\'+ song.replace('/','') + " Lyrics.txt", 'w+',encoding='UTF-8') as f:
                #     documents.append(lyrics.rstrip().strip())
                    # f.write(lyrics.rstrip().strip())
                    #
                    # print('')


    # # Нормализация списка строк
    normalized_texts = [normalize_text(text) for text in documents]
    morph_docs = []
    for normalized in normalized_texts:
        morph_docs.append(morph.normal_forms(normalized)[0])


    # Tokenize all documents
    tokenized_documents = [tokenize(doc) for doc in morph_docs]

    # Build the vocabulary
    vocabulary = set()
    for tokens in tokenized_documents:
        vocabulary.update(tokens)
    vocabulary = sorted(vocabulary)  # Sorting for consistent ordering


    # Compute TF
    tf = compute_tf(tokenized_documents, vocabulary)

    # Compute IDF
    idf = compute_idf(tokenized_documents, vocabulary)

    # Compute TF-IDF
    tfidf = compute_tfidf(tf, idf, vocabulary)

    # Display the results
    for idx, doc_tfidf in enumerate(tfidf):
        print(f"Document {idx + 1} TF-IDF:")
        for term, score in doc_tfidf.items():
            print(f"  {term}: {score:.4f}")
        print()