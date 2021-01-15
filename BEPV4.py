import pandas as pd
import time 
import requests
from bs4 import BeautifulSoup
import csv
from abydos import phonetic, distance

#################################### CREATING RANDOM CLIENTS DATASET #####################################
# Import the dataset of 10000 random client names
clients = pd.read_excel(r'C:\Users\daanv\Documents\TBK 4\BEP\Python\Complete Final Test Set.xlsx')
clients = clients.fillna(" ")
# Empty lists for the vectors of initials and letters
vec_of_initials = []
vecs_of_letters = []
fullnames = []
name_tokens = []
soundex_codes = []
meta_codes = []

# Create the vector of initials and vector of letters for each name
for i in clients.index:
    # Take the first letter of the first and last name and combine as lowercase string
    client = clients.iloc[i]
    if client["Name"][-1] != " ":
        s_name_init = client["Name"][client["Name"].rfind(" ")+1]
    else:
        s_name_init = " "
    initials = (client["Name"][0] + s_name_init).lower()
    sort_init = "".join(sorted(initials))
    vec_of_initials.append(sort_init)
    
    # Take the name and get all letters in the name as lowercase string
    fullname = client["Name"]
    fullnames.append(fullname)
    vec_of_letters = "".join(sorted(set(fullname))).lower()
    vecs_of_letters.append(vec_of_letters)
    
    # Split full name in tokens
    name_token = client["Name"].split(" ")
    for item in name_token:
        if item == " " or item == "":
            name_token.remove(item)
    name_tokens.append(name_token) 
    
    # Determine soundex codes
    soundex_code = []
    for item in name_token:
        code = phonetic.soundex(item)
        soundex_code.append(code)
    soundex_codes.append(soundex_code)  

    # Determine metaphone codes
    meta_code = []
    for item in name_token:
        code = phonetic.metaphone(item)
        meta_code.append(code)
    meta_codes.append(meta_code) 

# Add the new columns to the dataset     
clients["Full Name"] = fullnames 
clients["Name Tokens"] = name_tokens
clients["Soundex Codes"] = soundex_codes
clients["Metaphone Codes"] = meta_codes
clients["Vector of Initials"] = vec_of_initials
clients["Vector of Letters"] = vecs_of_letters

# Remove empty rows
clients = clients.fillna(" ")

# Convert the dataset to a dictionary
df_clients = clients
clients = clients.to_dict()

#################################### SANCTION LIST #####################################
# Import the sanction list 
s_list = pd.read_csv(r'C:\Users\daanv\Documents\TBK 4\BEP\Python\Sanction list.csv')
s_list = s_list.fillna(" ")

# Split full name in tokens
name_tokens = []
soundex_codes = []
meta_codes = []
for name in s_list["Full Name"]:
    name_token = name.split(" ")
    for item in name_token:
        if item == " " or item == "":
            name_token.remove(item)
    name_tokens.append(name_token)

    # Determine soundex codes
    soundex_code = []
    for item in name_token:
        code = phonetic.soundex(item)
        soundex_code.append(code)
    soundex_codes.append(soundex_code)  

    # Determine phonex codes
    meta_code = []
    for item in name_token:
        code = phonetic.metaphone(item)
        meta_code.append(code)
    meta_codes.append(meta_code) 
    
s_list["Name Tokens"] = name_tokens
s_list["Soundex Codes"] = soundex_codes
s_list["Metaphone Codes"] = meta_codes
     
# Convert the dataset to a dictionary
s_list = s_list.to_dict()

# Initiate lists
hit_or_not = [0]*len(clients["Full Name"])
scores = [""]*len(clients["Full Name"])
soundex_matches = [""]*len(clients["Full Name"])
phonex_matches = [""]*len(clients["Full Name"])

#################################### FUZZY-MATCHING ALGORITHM #####################################
def calculate_scores(s_list):
    """Compares the random clients dataset to different sanction lists"""
    global scores, hit_or_not
    
    # Initiate timer
    start_time = time.time()
    
    # Initiate empty list and variables to measure iterations
    x = 0
    y = 0
    z = 0
    
    # Compare each pair of client and entry in the sanction list
    for i in range(len(clients["Full Name"])):
        x += 1
        for j in range(len(s_list["Full Name"])):
            y += 1
            
            # Eliminate the pair if not one of the initials are the same
            if len(''.join(set(clients["Vector of Initials"][i]).intersection(s_list["Vector of Initials"][j]))) != 0:
                
                # Eliminate the pair if the number of different letters in the names is not the same
                if -3 < len(clients["Vector of Letters"][i]) - len(s_list["Vector of Letters"][j]) < 3:
                    
                    # Eliminate the pair if the names have more uncommon letters than common letters
                    if len(''.join(set(clients["Vector of Letters"][i]).intersection(s_list["Vector of Letters"][j]))) > len(''.join(sorted(set(clients["Vector of Letters"][i]) ^ set(s_list["Vector of Letters"][j])))):
                        
                        # Eliminate the pair if the number of uncommon letters is more than 2
                        if len(''.join(sorted(set(clients["Vector of Letters"][i]) ^ set(s_list["Vector of Letters"][j])))) < 5:
                            z += 1
                            
                            # Define the client and the entry on the sanction list in this pair
                            client = clients["Full Name"][i]
                            entry = s_list["Full Name"][j]
                            
                            # Determine soundex match
                            soundex = False
                            client_soundex = list(clients["Soundex Codes"][i])
                            entry_soundex = list(s_list["Soundex Codes"][j])
                            nr_tokens_client = len(client_soundex)
                            nr_tokens_entry = len(entry_soundex)
                            #print("Client: {}, C_token: {}, Entry: {}, E_token: {}".format(client, client_tokens, entry, entry_tokens))
                            common_tokens = len(set(client_soundex).intersection(entry_soundex))
                            if common_tokens == min(nr_tokens_client, nr_tokens_entry):
                                soundex = True
                            
                            # Determine metaphone match
                            phonex = False
                            client_phonex = list(clients["Metaphone Codes"][i])
                            entry_phonex = list(s_list["Metaphone Codes"][j])
                            nr_tokens_client = len(client_soundex)
                            nr_tokens_entry = len(entry_soundex)
                            #print("Client: {}, C_token: {}, Entry: {}, E_token: {}".format(client, client_tokens, entry, entry_tokens))
                            common_tokens = len(set(client_phonex).intersection(entry_phonex))
                            if common_tokens == min(nr_tokens_client, nr_tokens_entry):
                                phonex = True
                            
                            # Determine JW match
                            JW = False
                            client_tokens = clients["Name Tokens"][i]
                            entry_tokens = s_list["Name Tokens"][j]
                        
                            max_score = 0
                            for x in range(1, len(client_tokens)):
                                for y in range(1, len(entry_tokens)):
                                    jw_client = client_tokens[0] + " " + client_tokens[x]
                                    jw_entry = entry_tokens[0] + " " + entry_tokens[y]
                                    score = 1-distance.dist_jaro_winkler(jw_client, jw_entry)
                                    if score > max_score:
                                        max_score = score
                                        pair = "Client: {}, Entry: {}, JW: {}".format(jw_client, jw_entry, 1-distance.dist_jaro_winkler(jw_client, jw_entry))
                            if max_score > 0.85:
                                JW = True
                                
                            # Calculate the Soundex, Phonex and Jaro-Winkler distance
                            #soundex = phonetic.soundex(client) == phonetic.soundex(entry)
                            #jw_distance = distance.dist_jaro_winkler(client, entry)
                            #phonex = phonetic.phonex(client) == phonetic.phonex(entry)
                            
                            # Add the pair and their scores to the list of pairs
                            # Also add the average score
                            match = {"Client": clients["Full Name"][i], 
                                     "Entry": s_list["Full Name"][j], 
                                     "JW Score": JW,
                                     "Soundex": soundex,
                                     "Phonex": phonex,
                                     "Common Tokens": common_tokens
                                     }
                            
                            if JW == True:
                                scores[i] = match
                                
                            if soundex == True:
                                soundex_matches[i] = match
                                
                            if phonex == True:
                                phonex_matches[i] = match
                                
    
    # Print the time it took and the number of iterations
    print("--- It took the algorithm {}s seconds to check {}---".format(time.time() - start_time, "this list"))
    print("Amount of Clients = {}".format(x))
    print("Number of iterations = {}".format(y))
    print("Number of pairs to check = {}".format(z))
    print("")
    

# Use the algorithm on the different sanction lists
print("Entries Sanction List:{}".format(len(s_list["Full Name"])))
hits = calculate_scores(s_list)

# Add the columns to the dataframe
df_clients["Hit or not"] = hit_or_not
df_clients["JW Matches"] = scores
df_clients["Soundex Matches"] = soundex_matches
df_clients["Phonex Matches"] = phonex_matches

# Determine if the name is a tn, fp, fn or tp for Jaro_Winkler
anal_results = []
for i in range(len(df_clients["ID"])):
    case = df_clients.loc[i]["JW Matches"]
    if df_clients.loc[i]["Should be checked?"] == 0:
        if case == "":
            anal_results.append("TN")
        else:
            anal_results.append("FP")
    else:
        if case == "":
            anal_results.append("FN")
        else:
            anal_results.append("TP")

df_clients["Results JW"] = anal_results

# Compute the number of false\true positives\negatives in the results for Jaro-Winkler
nr_true_pos = sum(df_clients["Results JW"].str.count("TP"))
nr_false_pos = sum(df_clients["Results JW"].str.count("FP"))
nr_true_neg = sum(df_clients["Results JW"].str.count("TN"))
nr_false_neg = sum(df_clients["Results JW"].str.count("FN"))
print(nr_true_pos, nr_false_pos, nr_true_neg, nr_false_neg)

# Compute the precision and recall for Jaro-Winkler
precision_jw = nr_true_pos/(nr_true_pos + nr_false_pos)
recall_jw = nr_true_pos/(nr_true_pos + nr_false_neg)

# Print the different performance indicators
print("Precision JW: " + str(precision_jw))
print("Recall JW: " + str(recall_jw))
print("Number of true positives JW: " + str(nr_true_pos))
print("Number of false positives JW: " + str(nr_false_pos))
print("Number of true negatives JW: " + str(nr_true_neg))
print("Number of false negatives JW: " + str(nr_false_neg))

# Determine if the name is a tn, fp, fn or tp for Soundex
anal_results = []
for i in range(len(df_clients["ID"])):
    case = df_clients.loc[i]["Soundex Matches"]
    if df_clients.loc[i]["Should be checked?"] == 0:
        if case == "":
            anal_results.append("TN")
        else:
            anal_results.append("FP")
    else:
        if case == "":
            anal_results.append("FN")
        else:
            anal_results.append("TP")

df_clients["Results Soundex"] = anal_results

# Compute the number of false\true positives\negatives in the results for Soundex
nr_true_pos = sum(df_clients["Results Soundex"].str.count("TP"))
nr_false_pos = sum(df_clients["Results Soundex"].str.count("FP"))
nr_true_neg = sum(df_clients["Results Soundex"].str.count("TN"))
nr_false_neg = sum(df_clients["Results Soundex"].str.count("FN"))

# Compute the precision and recall for Jaro-Winkler
precision_soundex = nr_true_pos/(nr_true_pos + nr_false_pos)
recall_soundex = nr_true_pos/(nr_true_pos + nr_false_neg)

# Print the different performance indicators
print("Precision Soundex: " + str(precision_soundex))
print("Recall Soundex: " + str(recall_soundex))
print("Number of true positives Soundex: " + str(nr_true_pos))
print("Number of false positives Soundex: " + str(nr_false_pos))
print("Number of true negatives Soundex: " + str(nr_true_neg))
print("Number of false negatives Soundex: " + str(nr_false_neg))

# Determine if the name is a tn, fp, fn or tp for Soundex
anal_results = []
for i in range(len(df_clients["ID"])):
    case = df_clients.loc[i]["Phonex Matches"]
    if df_clients.loc[i]["Should be checked?"] == 0:
        if case == "":
            anal_results.append("TN")
        else:
            anal_results.append("FP")
    else:
        if case == "":
            anal_results.append("FN")
        else:
            anal_results.append("TP")

df_clients["Results Phonex"] = anal_results

# Compute the number of false\true positives\negatives in the results for Soundex
nr_true_pos = sum(df_clients["Results Phonex"].str.count("TP"))
nr_false_pos = sum(df_clients["Results Phonex"].str.count("FP"))
nr_true_neg = sum(df_clients["Results Phonex"].str.count("TN"))
nr_false_neg = sum(df_clients["Results Phonex"].str.count("FN"))

# Compute the precision and recall for Jaro-Winkler
precision_phonex = nr_true_pos/(nr_true_pos + nr_false_pos)
recall_phonex = nr_true_pos/(nr_true_pos + nr_false_neg)

# Print the different performance indicators
print("Precision Phonex: " + str(precision_phonex))
print("Recall Phonex: " + str(recall_phonex))
print("Number of true positives Phonex: " + str(nr_true_pos))
print("Number of false positives Phonex: " + str(nr_false_pos))
print("Number of true negatives Phonex: " + str(nr_true_neg))
print("Number of false negatives Phonex: " + str(nr_false_neg))
df_clients.to_csv(r'C:\Users\daanv\Documents\TBK 4\BEP\Python\Test Set with Results - Soundex - Phonex - JW.csv', encoding = 'utf-8-sig')

#print(s_list_nl["Vector of Initials"][10])



