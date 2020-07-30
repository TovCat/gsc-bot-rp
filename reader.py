
class WeatherText:

    def __init__(self):
        self.weather_strings = {}
        file = open("weather_text.txt", "r")
        contents = file.readlines()
        file.close()
        breaks = []
        for x in contents:
            if x[0] == "#":
                breaks.append(contents.index(x))
        for x in breaks:
            title = contents[x]
            i = x + 1
            string = contents[i]
            dict_list = []
            while string != "":
                dict_list.append(string)
                i += 1
                string = contents[i]
            self.weather_strings[title] = dict_list
