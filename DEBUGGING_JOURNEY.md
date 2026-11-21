# Debugging Journey

This is what went wrong while building the agent layer, how I worked out why, and what I took from each problem. I used an AI assistant to plan and discuss, and Kiro to generate code, however the initial ETL pipelines, first tool, testing and the "what is actually happening here" detective work here was mine so I could learn and keep track of it.

## Before the bugs: choosing the API

I first decided to use Gemini's plain text generation. After searching and asking an AI assistant to compare options, I went with the Interactions API after finding out how this API will support tool calling in a clean way. That choice taught me that each project decides which API fits, and that I need to read the docs and adapt the sample request myself. I wrote the headers, body and `requests.post` call by hand instead of using the client library, so I would know exactly what gets sent.



\---

## 1\. Weeks of 503 errors

**What I saw.** The agent worked once with the very first tool (search\_products) and ETL Pipeline I designed, then every request returned `service\\\_unavailable`. I assumed it was temporary.

**What I did.**

1. I opened the API URL from the error message in my browser and got a **403 PERMISSION\_DENIED**. That looked alarming, but a browser sends a GET with no key, while my code sends a POST with a key, so it proved nothing.
2. I wrote a small script that sent the real POST and printed the raw status and body. It returned 503 and named a specific model: `gemini-3.8-flash` was "experiencing high demand".
3. I listed models with my key. That returned 200, so the key was fine, and the model was listed.
4. I tried other models on the same endpoint. The 2.5 models returned **404, no longer available to new users**. One other model returned 503 as well, and another did not answer for 30 seconds and crashed my script with a long timeout traceback. I even created multiple Test\_gemini files, but soon found it way too complicated and searched the overload
5. I searched for whether the Interactions API was struggling, and found other developers reporting severe 503s.
6. I switched the model to `gemini-3-flash-preview` and got a 200.

**Cause.** An overloaded model on an experimental endpoint. I cannot say whether the endpoint or just that model was the problem.

**What I took from it.** Read the real status and body before guessing. A 503 (try later), a 404 (will never work) and a 403 (permission) need different responses, and my code at the time could not tell them apart. I also noticed I was writing a new throwaway script for every question, so I stopped and simplified. This investigation is what turned error handling from a nice-to-have into the next task.

## 2\. The error handler that crashed

**What I saw.** I temporarily broke my API key to test the failure path. Instead of a clean message I got `AttributeError: 'list' object has no attribute 'get'`, inside the code meant to handle the error.

**Cause.** My handler assumed Google's error body was a dictionary. This time it was a list of dictionaries (my very first browser 403 had the same shape, and I had not connected the two).

**Fix.** A small helper that checks the type before reading it, and falls back to the raw text.

**What I took from it.** Error-handling code has bugs too, and you only find them by triggering failures on purpose. After the fix, the broken key returned a 401 immediately with no retries, which is the behaviour I wanted.

## 3\. The response position I trusted

**What I saw.** The original code used `result\\\["steps"]\\\[1]` to find the model's answer and this was since designed with the very first tool (the output was a simple dict so i assumed it would be the same everytime lol). And since tt worked every time, so I did not question it.

**What I found.** After few errors, I printede full response and saw that `steps\\\[0]` was a `thought` step and the tool call was second. That position only worked because there was exactly one thought step. If the model skipped thinking, `steps\\\[1]` would crash, and if it thought twice, I would silently read the wrong step.

**Fix.** Find the step by its `type` (`function\\\_call`, or `model\\\_output` for text). This also fixed a second gap: a plain "hello" with no tool used to crash, and now returns text.

**What I took from it.** Code that works is not the same as code that is correct. Look at the real data before trusting a hardcoded position.

## 4\. A question that needed more than one tool

**What I saw.** "What orders did Emily place?" failed with "expected a text response but got a function\_call".

**Cause.** My agent allowed exactly one tool round. Gemini wanted to look up the orders and then open each one.

**Fix.** A loop in `agent.py` that keeps going until Gemini replies with text, capped at 5 rounds. The cap is there because the loop's exit depends on the model's decision, which I do not control. It is the same reasoning as the 3-attempt limit on retries.

**What I took from it.** I could not tell from the error which tool Gemini asked for, so I added a print of the tool name and arguments. Later it showed three calls for that question: one for the orders, then one per order.

## 5\. A total that was $1 wrong

**What I saw.** For one order, Gemini reported a total of $1,119.23. Adding the line items by hand gave $1,120.23.

**Cause.** I had no total tool, so Gemini added the numbers itself, and language models are not reliable at arithmetic.

**What I first got wrong.** I assumed the new `get\\\_order\\\_total` tool existed and Gemini was ignoring it. When I checked the three places a tool has to exist (the function, the registry, the `tools` list), it was not in any of them. It had never been built.

**Fix.** I built it so the database does the sum, and wrote the description to tell Gemini to use it for totals. With debug prints on, a question about order 104 called `get\\\_order\\\_total` directly and returned $1,120.23.

**What I took from it.** Check that something exists before debugging how it behaves. Also, Gemini chooses tools by reading their descriptions, so the wording works like code.

\---

## Smaller problems

|Problem|Cause|What I learned|
|-|-|-|
|`tuple index out of range`|I removed two columns from a SELECT but the Python loop still read them by position|The query and the code reading its rows have to change together|
|`amount` and `status` null everywhere|My ETL never inserted them, and the source data has no status|A schema shows which columns exist, not whether they contain data|
|`products.name` null|The data is in `title`|Look at real rows before choosing which column to use|
|I wanted to drop a planned tool|`get\\\_orders\\\_by\\\_status` would filter on a column that is always null|Finding that out before building saved work|
|I commented out error prints along with debug prints|Both were `print` calls, but one explains why a connection failed|Debug output and error messages are different things, so I labelled them `# DEBUG:` and `# KEEP:`|
|"Only 100 customers"|The table viewer pages at about 100 rows; a count query showed 208|Verify with a query, not with how a screen looks|

## One thing pending

In one run, Gemini listed items under Emily Brown's order 103 that did not match what the database held when I checked it afterwards (Cat Food, Red Onions and Soft Drinks). I never pinned down why. Because of that I keep the `DATABASE RESULT BEING SENT` debug print ready, so I can tell whether a wrong answer came from the database or from the model.

## What I would do differently

* Test the failure paths when I first write the happy path, not after.
* Print the raw response early, before writing parsing code.
* Check what is in the data, not only what the schema says.
* Write one small test for each tool, so I do not rely on asking questions by hand.

