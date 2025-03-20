import asyncio

from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright

import json

from dotenv import load_dotenv
import os

ADDRESS = {
    "Country": "Canada",
    "Street Address": "200 University Avenue West",
    "City": "Waterloo",
    "Province/Territory": "Ontario",
    "Postal code": "N2L 3G1"
}

async def get_scrapybara_browser():
    client = Scrapybara(api_key=os.getenv("SCRAPYBARA_API_KEY"))
    instance = client.start_browser()
    return instance


async def handle_response(response, menu_items):
    print(response.url)
    if ("https://www.doordash.com/graphql/itemPage?operation=itemPage" == response.url): # filters for network responses resulting from clicking menu items
        item_data = await response.json() # stores menu item data as a dictionary
        item_name = item_data['data']['itemPage']['itemHeader']['name'] # extracts menu item name

        menu_items.append({item_name: item_data}) # adds the menu item data to the menu items list


async def enter_address(page):
    await page.get_by_text("Enter address").click() # clicks the underlined 'Enter address'

    await page.get_by_placeholder("Address").nth(1).fill(ADDRESS["Street Address"]) # enters street address info

    await page.locator("span[data-testid='ManualAddressEntryButton']").click() # clicks on 'Enter address manually' option

    await page.get_by_label('Country').select_option(ADDRESS["Country"]) # selects Canada for country

    await page.get_by_label('Street Address').fill(ADDRESS["Street Address"]) # enters street address info
 
    await page.get_by_label('City').fill(ADDRESS["City"]) # enters city info

    await page.get_by_label('Province/Territory').fill(ADDRESS["Province/Territory"]) # enters province info

    await page.get_by_label('Postal code').fill(ADDRESS["Postal code"]) # enters postal code info

    await page.locator("button[data-testid='manual-address-form-submit']").click() # clicks the 'Continue' button

    await page.locator("button[data-testid='manual-address-confirmation-btn']").click() # clicks the 'Confirm' button

    await page.locator("button[data-anchor-id='AddressEditSave']").click() # clicks the 'Save' button

    await page.get_by_text("See Menu").click() # clicks the 'See Menu' button


async def retrieve_menu_items(instance, start_url: str) -> list[dict]:
    """
    :args:
    instance: the scrapybara instance to use
    url: the initial url to navigate to

    :desc:
    this function navigates to {url}. then, it will collect the detailed
    data for each menu item in the store and return it.

    (hint: click a menu item, open dev tools -> network tab -> filter for
            "https://www.doordash.com/graphql/itemPage?operation=itemPage")

    one way to do this is to scroll through the page and click on each menu
    item.

    determine the most efficient way to collect this data.

    :returns:
    a list of menu items on the page, represented as dictionaries
    """
    cdp_url = instance.get_cdp_url().cdp_url
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page(
            viewport={"width":1728, "height":9999} # height = 9999 makes visible all clickable menu items on the page
        )

        await page.goto(start_url)

        # browser automation ...

        menu_items = [] # initializes menu items list

        page.on("response", lambda response: handle_response(response, menu_items)) # intercepts network responses when menu items are clicked

        await enter_address(page) # enters address info so that menu items can be clicked on

        # clicks on every menu item using class='sc-761095a3-2 jXhKue', saves a screenshot for reference, and then closes the popup 
        for i in range(await page.locator("div[class='sc-761095a3-2 jXhKue']").count()):
            await page.locator("div[class='sc-761095a3-2 jXhKue']").nth(i).click()
            # await page.wait_for_timeout(1000)
            # await page.screenshot(path=f"menuItem{i+1}.png")
            await page.get_by_role("button", name="Close").click()
        
        await browser.close() # closes browser

        return menu_items # returns list of menu items


async def main():

    load_dotenv() # load environment variables from .env file

    instance = await get_scrapybara_browser()

    try:
        data = await retrieve_menu_items(
            instance,
            "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false",
        )

        with open("results.json", 'w') as file: # saves menu data in a JSON file
            file.write(json.dumps(data))
        
    finally:
        # Be sure to close the browser instance after you're done!
        instance.stop()


if __name__ == "__main__":
    asyncio.run(main())
