#############################################################
#           asynchronous python web scraper using:          #
#         GoBuster, aiohttp, asyncio, beautifulSoup         #
#                     By:Shon Grinberg                      #
#############################################################


import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup


#parse page html (soup)
def parse(soup):
    #here you will parse for whatever you need
    #In this example we search for text boxes and return their 'name' property
    try:
        found = [_input['name'] for _input in  soup.find_all('input') if _input['type'] in ['text','password','email']]

    #catch errors from inputs which don't have a 'type' attribute
    except KeyError as e:
        return None

    return found

#create a process for command and pass it to processing function
async def run_command_shell(command):
    # Create subprocess
    process = await asyncio.create_subprocess_shell(command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    # Status
    print(f'Started: {command} (pid =  {process.pid} + )')

    #process live output
    await process_live_output(process)

# Initialize a semaphore object with a limit
#this will limit the concurrency to make sure we don't over-request
limit = asyncio.Semaphore(4)

#process live output from cmd process
async def process_live_output(process):

    # Wait for the subprocess to finish
    #await stdout !=0
    while True:
        line = await process.stdout.readline()
        if 'Started: ' not in line.decode():
            url = line.decode().strip().replace('Found: ', '')
            if url != '':
                async with limit:
                    await get_site_content('https://' + url)
                    # When workers hit the limit, they'll wait for a second
                    # before making more requests.
                    if limit.locked():
                        print("Concurrency limit reached, waiting ...")
                        await asyncio.sleep(1)
        if not line:
            break

#get site's html and pass it to parser
async def get_site_content(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                text = await resp.read()

            loop = asyncio.get_event_loop()
            soup = BeautifulSoup(text.decode('utf-8'), 'lxml')
            items = await loop.run_in_executor(None,parse,soup) #pass html to parse function
            if items is not None and items != []:
                print(f"Found in: {url}\n{items}")
        except aiohttp.ClientConnectionError as e:
            print(f'Invalid url on: {e}')

#Run tasks asynchronously using asyncio and return results
async def run_asyncio_commands(tasks):
    all_results = []
    results = await asyncio.gather(*tasks)  # Unpack list using *
    all_results += results
    return all_results;



async def main():
    #start timer
    start = time.time()
    #commands to run
    cmds = ["gobuster dns -d google.com -w C:/wordlists/login.txt -t 50 --quiet",
            "gobuster dns -d yahoo.com -w C:/wordlists/login.txt -t 50 --quiet",
            "gobuster dns -d facebook.com -w C:/wordlists/login.txt -t 50 --quiet"]

    #create async tasks with commands
    tasks = []
    for command in cmds:
        tasks.append(run_command_shell(command))

    await run_asyncio_commands(tasks)
    #end timer and display
    end = time.time()
    rounded_end = ('{0:.4f}'.format(round(end-start,4)))
    print(f'Script ran in about {rounded_end} seconds')


asyncio.get_event_loop().run_until_complete(main())
