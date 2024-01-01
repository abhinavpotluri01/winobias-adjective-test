# This file just served as a place for me to write down all my commands without having to go through them one by one with the command line
# Whenever I was done with the previous commands and ready for the next ones, I would delete what was there and rewrite
# So what's left is what was last


import prompt
import completion
import data
import time
import json
import parallel
import asyncio  # for running API calls concurrently
import logging  # for logging rate limit warnings and other messages
import os  # for reading API key
import re  # for matching endpoint from request URL
import tiktoken  # for counting tokens
from dataclasses import (
    dataclass,
    field,
)  # for storing API inputs, outputs, and metadata


adjList = ["pro_base", "anti_base",
        "pro_arrog-respo", "anti_arrog-respo",
        "pro_brill-busy", "anti_brill-busy",
        "pro_dry-bubbl", "anti_dry-bubbl",
        "pro_funny-stric", "anti_funny-stric",
        "pro_hard-soft", "anti_hard-soft",
        "pro_intel-sweet", "anti_intel-sweet",
        "pro_knowl-helpf", "anti_knowl-helpf",
        "pro_large-littl", "anti_large-littl",
        "pro_nothi-blond", "anti_nothi-blond",
        "pro_nothi-mean", "anti_nothi-mean",
        "pro_old-nothi", "anti_old-nothi",
        "pro_organ-disor", "anti_organ-disor",
        "pro_polit-nothi", "anti_polit-nothi",
        "pro_pract-pleas", "anti_pract-pleas",
        "pro_tough-under", "anti_tough-under"
    ]
prompts_files = [None] * 32
completions_files = [None] * 32
headings = [None] * 32


def run(trialNum):
    print("Running...")
    
    readAdj(trialNum)
    runParallelCompletions()
    runStats(trialNum)
    runHeatMap(trialNum)
    
    print("Done!")
    
    
def readAdj(trialNum):
    start = time.time()
    numRows = 395
    for i in range( len(adjList) ):
        prompts_files[i] = "prompts\\promp_type1_" + adjList[i] + ".txt.test"
        completions_files[i] = "completions\\trial" + str(trialNum) + "\\compl_tri" + str(trialNum) + "_type1_" + adjList[i] + ".txt.test"

        tokens = adjList[i].split("_")
        headings[i] = "I"
        for j in range( len(tokens) ):
            headings[i] += " " + tokens[j].title() # title() is used over capitalize() so that the letter after the hyphen is also uppercase
    
    end = time.time()
    print("readAdj time: ", end - start)
    

def runPrompts():
    print()

def runCompletions():
    modelName = "gpt-3.5-turbo"
    numRows = 395
        
    for i in range( len(prompts_files) ):
        start = time.time()
        completion.getCompletionsOf(prompts_files[i], completions_files[i], modelName, headings[i], numRows)
        printSeparator("Completed File " + str(i + 1))
        end = time.time()
        print("in runCompletions iteration: ", i, " time: ", end - start)

def runParallelCompletions():
    numRows = 395
    
    for i in range( len(prompts_files) ):
        start = time.time()
        printSeparator(headings[i])
        actualPrompt = [None] * numRows
        messages = [None] * numRows
        completions = [None] * numRows
        responseMessages = [None] * numRows
        with open(prompts_files[i], "r") as file:
            for j in range(numRows):
                actualPrompt[j] = file.readline().strip()
                messages[j] = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": actualPrompt[j]}]} #, "input": str(j)}
        with open("input.json1", "w") as file:
            for j in range(numRows):
                file.write(json.dumps(messages[j]) + "\n")
            printSeparator("Completed File " + str(i + 1))
        
        asyncio.run(
            parallel.process_api_requests_from_file(
                requests_filepath="input.json1", #"C:/Users/abhin/Prompt OpenAI/winobias-adjective-test/input.json1", #args.requests_filepath,
                save_filepath="results.json1", #"C:/Users/abhin/Prompt OpenAI/winobias-adjective-test/results.json1", #args.save_filepath,
                request_url="https://api.openai.com/v1/chat/completions", #args.request_url,
                api_key=os.getenv("API_KEY"), #args.api_key,
                max_requests_per_minute=float(3_000 * 0.5),
                max_tokens_per_minute=float(250_000 * 0.5),
                token_encoding_name="cl100k_base",
                max_attempts=int(6),
                logging_level=int(logging.INFO),
            )
        )
        #process results.json1 and write to completions[i] with headings[i]
        # Extract entire message content
        with open("results.json1", "r") as file:
            for j in range(numRows):
                #print(file.readline().strip())
                line = json.loads(file.readline().strip())
                responseMessages[j] = line[1]['choices'][0]['message']['content']
        
                # Take only the first word of the response
                tokens = responseMessages[j].split()
                if tokens[0] == "the" and len(tokens) == 2: # Make an exception for 'the _____'
                    extraction = tokens[1]
                else:
                    extraction = tokens[0]
            
                # Remove whitespace, punctuation, and capitalization
                extraction = extraction.strip()
                extraction = extraction.strip(".")
                extraction = extraction.lower()
        
                completions[j] = extraction   
                #print("completions[j]: ", completions[j])     
        print("Completed request " + str(i + 1))

        # Output completions to csv
        with open(completions_files[i], "w") as file:
            file.write(headings[i] + "\n")
            for line in completions:
                file.write(line + "\n")
        #exit()
        end = time.time()
        print("Time taken for file[",i,"]: ", end - start)
        time.sleep(25)

def runStats(trialNum):
    for i in range( len(completions_files) ):
        start = time.time()
        completions_files[i] = completions_files[i]
        end = time.time()
        print("in runStats iteration: ", i, " time: ", end - start)
    
    data.makeStatsFile("answers\\coranswers.txt.test", "answers\\incanswers.txt.test", completions_files, "output\\output_data_tri" + str(trialNum) + ".csv", 395)
    
 
def runHeatMap(trialNum):
    data.makeHeatMap("answers\\coranswers.txt.test", "answers\\incanswers.txt.test", "output\\output_data_tri" + str(trialNum) + ".csv",
        "output\\output_heat_tri" + str(trialNum) + ".csv", 395, 32)
    
    
    
def printSeparator(message):
    print("\n\n")
    print("------------------------------")
    print("******************************")
    print(message)
    print("------------------------------")
    print("******************************")
    print("\n\n")

if __name__ == "__main__":
    run(1)