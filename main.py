import discord
import json
import os
import random
import requests

from discord.ext import commands
# from discord.utils import get

INTENTS = discord.Intents.default()
INTENTS.message_content = True

c_key = None  # str
c_secret = None  # str
bot = None  # obj
products = None  # dict
admins = None  # list

SITE_LINK = 'https://eudoramods.com'
LOGO_LINK = f'{SITE_LINK}/wp-content/uploads/2024/02/cropped-Eudora_big.png'
SETTINGS_PATH = os.getcwd() + '\\EudoraBot\\settings\\'
MISC_PATH = os.getcwd() + '\\EudoraBot\\misc\\'
LICENSE_STATUS = {
    1: "sold",
    2: "delivered",
    3: "active",
    4: "inactive"
}
PRODUCT_ID = {
    None: "invalid",
    375: "midnight",
    91: "memesense",
    377: "fecurity"
}


def get_all_licenses() -> dict:
    response = requests.get(ENDPOINTS['generic'])
    return response.json()


def get_license_information(license: str) -> dict:
    response = requests.get(ENDPOINTS['specific'].format(license))
    return response.json()['data']


def add_license(license: str, product: str, status: str = 'active'):
    data = {'license_key': license, 'status': status, 'product_id': products[product], 'times_activated_max': 1}
    response = requests.post(ENDPOINTS['generic'], json=data)

    return response.status_code


def remove_license(license: str):
    response = requests.delete(ENDPOINTS['specific'].format(license))
    return response.status_code


def update_license_status(license: str, status: str) -> int:
    endpoint = ENDPOINTS['specific'].format(license)
    data = {'license_key': license, 'status': status}
    response = requests.put(endpoint, json=data)

    return response.status_code


def generate_licenses(product: str, amount: int) -> list:
    licenses = get_all_licenses()
    product_num = products[product]
    results = []

    for data in licenses['data']:
        product_id = data['productId']
        status = data['status']

        if product_id == product_num and status == 3:
            results.append(data)

    return random.sample(results, amount)


def build_embed(title, purchasing: bool = True) -> discord.Embed:
    if purchasing:
        description = 'Thank you for purchasing! Here are your key(s):'
    else:
        description = "EudoraMods miscellaneous."

    embed_builder = discord.Embed(
        title=title,
        url=SITE_LINK,
        description=description,
        color=0xff0d55
    )
    embed_builder.set_author(name='EudoraMods', url=SITE_LINK, icon_url=LOGO_LINK)
    embed_builder.set_thumbnail(url=LOGO_LINK)
    embed_builder.set_footer(text=f'{SITE_LINK} | Software Resellers')

    return embed_builder


if __name__ == '__main__':
    with open(SETTINGS_PATH + 'config.json', 'r') as f:
        config = json.load(f)

        prefix = config['prefix']
        token = config['token']
        c_key = config['consumer_key']
        c_secret = config['consumer_secret']

    with open(SETTINGS_PATH + 'admins.json', 'r') as f:
        admins = json.load(f)

    with open(MISC_PATH + 'products.json', 'r') as f:
        products = json.load(f)

    ENDPOINTS = {
        'generic': f'{SITE_LINK}/wp-json/lmfwc/v2/licenses?consumer_key={c_key}&consumer_secret={c_secret}',
        'specific': f'{SITE_LINK}/wp-json/lmfwc/v2/licenses/{{0}}?consumer_key={c_key}&consumer_secret={c_secret}'
    }

    bot = commands.Bot(command_prefix=prefix, intents=INTENTS)


@bot.event
async def on_ready():
    print('Bot started.')


@bot.event
async def on_message(message):
    if message.author.id in admins:
        await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.command()
async def generate(ctx, product: str, amount: str):
    license_json = generate_licenses(product, int(amount))
    embed_builder = build_embed(f'{amount}x {product}')

    for data in license_json:
        embed_builder.add_field(name='KEY', value=data['licenseKey'], inline=False)

    await ctx.send(embed=embed_builder)
    await ctx.message.delete()


@bot.command()
async def create(ctx, license: str, product: str, status: str = 'active'):
    response = add_license(license, product, status)
    await ctx.send(f"Operation completed. Status code: {response}")


@bot.command(aliases=['delete'])
async def remove(ctx, license: str):
    response = remove_license(license)
    await ctx.send(f"Operation completed. Status code: {response}")


@bot.command(aliases=['change'])
async def update(ctx, license: str, status: str):
    response = update_license_status(license, status)
    await ctx.send(f"Operation completed. Status code: {response}")


@bot.command(aliases=['status'])
async def check(ctx, license: str):
    data = get_license_information(license)
    embed_builder = build_embed('EudoraMods Website', False)

    embed_builder.add_field(name='Product', value=PRODUCT_ID[data['productId']], inline=False)
    embed_builder.add_field(name='License', value=license, inline=False)
    embed_builder.add_field(name='Status', value=LICENSE_STATUS[data['status']], inline=False)
    embed_builder.add_field(name='Order ID', value=data['orderId'], inline=False)

    await ctx.send(embed=embed_builder)
    await ctx.message.delete()


@bot.command(aliases=['give'])
async def manual(ctx, product: str, license: str):
    embed_builder = build_embed('EudoraMods Website')

    embed_builder.add_field(name='KEY', value=license, inline=True)

    await ctx.send(embed=embed_builder)
    await ctx.message.delete()

bot.run(token)
