# Sendvalu money transfer task

## Description of the project

This task is about obtain list of countries, that allow certain other 
countries to send them money through https://www.sendvalu.com/en/ service,
then writing the result to postgres database table.
<br><br>
The same task was accomplished twice, with the simple and asynchronous
versions. For second purpose we used aiohttp and asyncio libraries.
<br><br>
Difference between runtimes:
<ul>
    <li>
        Synchronous version: about 2-3 minutes
    </li>
    <li>
        Asynchronous version: 13.9 seconds
    </li>
</ul>




