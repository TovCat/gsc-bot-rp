import discord
from discord.ext import commands, tasks
import numpy as np
from datetime import date
import os


def G(x, sigma, mu):
    return 1 / (sigma * np.power(2 * np.pi, 0.5)) * np.exp(-0.5 * ((x - mu) ** 2 / sigma ** 2))


def weather_conditions():
    min_temp = [-9.1, -8, -3.5, 3.7, 9.3, 12.6, 13.7, 12.9, 8.6, 3.8, -0.7, -5.1]
    max_temp = [-3.0, -1.4, 3.7, 13.2, 20.3, 23.5, 24.6, 23.9, 18.8, 11.8, 4.3, -0.1]
    average_temp = [-6.1, -4.7, 0.1, 8.4, 14.8, 18, 19.1, 18.4, 13.7, 7.8, 1.8, -2.6]
    # шкала Бофорта скоростей ветра
    beaufort_ws = [0.2, 1.5, 3.3, 5.4, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4]
    # шансы выпадания определенных диапазонов скоростей ветра (накидано на глаз)
    beaufort_ws_weights = [0.035, 0.05, 0.15, 0.215, 0.255, 0.15, 0.09, 0.0325, 0.02, 0.002, 0.0005]
    # шансы выпадения диапазонов ветра, если идет дождь (когда идет дождь - ветер должен быть сильнее)
    beaufort_ws_weights_rain = [0.0, 0.0, 0.15, 0.20, 0.28, 0.17, 0.1, 0.0425, 0.035, 0.015, 0.0075]
    # 0 - ясно, 1 - переменная облачность, 2 - облачно с прояснениями, 3 - пасмурно, 4 - туман, 5 - дождь, 6 - ливень
    w_cond_weight = [0.35, 0.25, 0.125, 0.125, 0.001, 0.1, 0.049]
    # "сила" дождя: 0 - моросящий дождь, 1 - обычный дождь, 2 - почти ливень
    rain_power_weight = [0.2, 0.7, 0.1]
    # "сила ливня: 0 - ливень, 1 - гроза
    hale_power_weight = [0.8, 0.2]
    # шанс на "порывы ветра"
    wind_burst_weight = [0.4, 0.3, 0.23, 0.07]

    today = date.today()
    average_temp_today = average_temp[today.month - 1]
    width = round(abs(min_temp[today.month - 1]) * 10 + abs(max_temp[today.month - 1]) * 10) + 1
    temp_distribution = np.linspace(min_temp[today.month - 1], max_temp[today.month - 1], width)
    temp_sigma = (max_temp[today.month - 1] - min_temp[today.month - 1]) / 2  # три сигма
    prob = np.zeros((width))
    sum_g = 0.0
    for i in range(temp_distribution.shape[0]):
        x = temp_distribution[i]
        prob[i] = G(x, temp_sigma, average_temp_today)
        sum_g += prob[i]
    prob = prob / sum_g
    temp = np.random.choice(temp_distribution, p=prob)
    # 0 - север, далее по часовой стрелке
    wind_destination = round(np.random.uniform(0.0, 7.0))
    w_cond = np.random.choice(list(range(7)), p=w_cond_weight)
    r_p = 0
    if w_cond == 4:
        r_p = np.random.choice(list(range(3)), p=rain_power_weight)
    elif w_cond == 5:
        r_p = np.random.choice([0, 1], p=hale_power_weight)
    if w_cond == 4 or w_cond == 5:
        ws_interval = beaufort_ws.index(np.random.choice(beaufort_ws, p=beaufort_ws_weights_rain))
        ws = round(np.random.uniform(beaufort_ws[ws_interval - 1], beaufort_ws[ws_interval]))
    else:
        ws_interval = beaufort_ws.index(np.random.choice(beaufort_ws, p=beaufort_ws_weights))
        if ws_interval == 0:
            ws = round(np.random.uniform(0.1, beaufort_ws[ws_interval]), 1)
        else:
            ws = round(np.random.uniform(beaufort_ws[ws_interval - 1], beaufort_ws[ws_interval]))
    temp -= ws * np.random.uniform(0, 0.25)
    temp = int(round(temp))
    wind_burst = np.random.choice(list(range(3, 7)), p=wind_burst_weight)
    return temp, w_cond, r_p, ws, ws_interval, wind_destination, wind_burst


def compose(temp, w_cond, r_p, ws, wind_destination, wind_burst):
    greeting = ["Доброе утро сталкеры! Передаю прогноз погоды на сегодня.",
                "На связи профессор Сахаров. Прогноз погоды на сегодня.",
                "На связи Сахаров.",
                "Приветствую сталкеры, на связи Профессор Сахаров.",
                "Прием, говорит Профессор Сахаров.",
                "Приём, на связи Профессор Сахаров."]
    w_cond_str = [["Весь день будет ясная погода.",
                   "Сегодня нас ждет ясная погода, на небе ни облачка.",
                   "Погода сегодня отличная: ясная и солнечная!",
                   "Сегодня весь день будет ясно - отличная погода, чтобы размять ноги!"],
                  ["Сегодня ожидается переменная облачность.",
                   "Погода сегодня преимущественно ясная, с редкой облачностью.",
                   "Сегодня возможна небольшая облачность, но в целом день будет ясный."],
                  ["Практически весь день будет облачно, с небольшими прояснениями.",
                   "Небо медленно затягивается облаками, но иногда возможны небольшие просветы.",
                   "Погода постепенно портится - почти весь день будет пасмурно."],
                  ["Погода сегодня пасмурная, небо затянуто плотными облаками.",
                   "Сегодня весь день ожидается облачность, но хотя бы без дождя - и то хорошо.",
                   "Сегодня небо над Зоной будет плотно затянуто облаками."],
                  ["Сегодня над Зоной туман - видимость очень ограниченная!",
                   "Сегодня Зона 'одарила' нас крайне необычным явлением: весь день ожидается плотный туман."]]
    rains_str = [["Моросящий дождь.", "Время от времени будет идти слабый дождь."],
                 ["Ожидается дождь."],
                 ["Ожидается сильный дождь - берегите ноги!"]]
    hale_str = [["Ожидается ливень!"],
                ["Ожидается сильный ливень с грозой: соблюдайте меры осторожности!"]]
    wind_destination_str = ["северный", "северо-восточный", "восточный", "юго-восточный", "южный", "юго-западный",
                            "западный", "северо-западный"]
    prognoz = "```\n"
    prognoz += greeting[np.random.choice(list(range(len(greeting))))]
    if 4 >= w_cond >= 0:
        prognoz += " " + w_cond_str[w_cond][np.random.choice(list(range(len(w_cond_str[w_cond]))))]
    elif w_cond == 5:
        prognoz += " " + rains_str[r_p][np.random.choice(list(range(len(rains_str[r_p]))))]
    elif w_cond == 6:
        prognoz += " " + hale_str[r_p][np.random.choice(list(range(len(hale_str[r_p]))))]
    prognoz += " " + f"Температура воздуха: {temp} градусов."
    if ws > 0:
        prognoz += " " + f"Ветер - {wind_destination_str[wind_destination]}, {ws} м/с с порывами до {ws + wind_burst} м/с."
    else:
        prognoz += " " + "Штиль."
    if ws >= 17:
        prognoz += " " + "Штормовое предупреждение!"
        if 17 <= ws <= 20:
            warning_pool = ["Ломаются ветки деревьев, против ветра идти очень трудно.",
                            "Стволы деревьев качаются, ломаются ветки.",
                            "Идти против ветра сложно, ломаются сучья на деревьях."]
        elif 20 < ws <= 24:
            warning_pool = ["Ветер срывает черепицу с кровель зданий, ломает деревья.",
                            "Ветер повреждает крыши зданий и деревья.",
                            "Ветер наносит серьезные повреждения зданиям и деревьям, в воздухе летают мелкие обломки."]
        elif ws > 24:
            warning_pool = ["Ветер значительно повреждает здания, вырывает деревья с корнем.",
                            "Возможны серьезные разрушения, вплоть до обрушения нестабильных зданий.",
                            "В воздухе летают крупные обломки, ветки, здания рушатся."]
        prognoz += " " + warning_pool[np.random.choice(list(range(len(warning_pool))))] + " " + \
                   "Соблюдайте осторожность и не выходите на открытую местность без особой нужды!"
    prognoz += "\n```"
    return prognoz


def diceparser(n, d, p):
    r = []
    sum = 0
    choice = list(range(1, d+1))
    for i in range(n):
        num = np.random.choice(choice)
        r.append(num)
        sum += num + p
    return r, sum


client = commands.Bot(command_prefix=".")


@client.event
async def on_ready():
    print("Bot is ready")


@client.command()
async def weather(ctx):
    temp_out, w_cond_out, r_p_out, ws_out, ws_interval_out, wind_destination_out, wind_burst_out = weather_conditions()
    await ctx.send(compose(temp_out, w_cond_out, r_p_out, ws_out, wind_destination_out, wind_burst_out))


client.run(os.environ['TOKEN'])
