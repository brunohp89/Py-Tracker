# pip install python-binance requests forex-python pydrive pandas==1.3.1 numpy pycoinbase currencyconverter coinbase mplfinance
import importlib
import sys

import numpy as np
import addpath
import json
import tkinter as tk
import tracker_library as tl
import pickle as pk
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import utiltools
from datetime import timezone
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import datetime as dt
import mplfinance as mpf
import logging

# TODO: general -> give more meaningful names to labels and buttons
# TODO: general -> remove some redundant attributes in some classes

version = "Version 2021-09-30"

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='executionlog.log',
                    level=logging.NOTSET)
logging.warning(msg=f'Execution started. tracker_library {tl.version}, Main {version}')

foreground = 'white'
background = 'black'
main_window = tk.Tk()
main_window.configure(bg=background)
canvas_height = 110


# ------------------------------------------------------------ #
#                   For first use                              #
# ------------------------------------------------------------ #

def restart():
    main_window.destroy()
    import main
    importlib.reload(main)


if len(tl.setup) == 0:
    class FirstUseWindow:
        def __init__(self, root):
            self.root = root
            self.label_first = tk.Label(self.root,
                                        text="Looks like it's your first time here, click on the button below to add "
                                             "your accounts info. Click Restart Program when done.", bg=background,
                                        fg=foreground)
            self.label_first.pack()
            self.button = tk.Button(main_window, text="Update accounts information", command=self.add)
            self.button.pack()
            self.button2 = tk.Button(main_window, text="Restart program", command=restart)
            self.button2.pack()

        def add(self):
            window3 = tk.Toplevel(bg=background)
            self.var1 = tk.IntVar()
            self.var2 = tk.IntVar()
            self.name = tk.Entry(window3, text="Name")
            labelname = tk.Label(window3, text="Account Name", bg=background, fg=foreground)
            self.network = tk.Entry(window3, text="Network")
            labelnetwork = tk.Label(window3, text="Network", bg=background, fg=foreground)
            self.token = tk.Entry(window3, text="Token")
            labeltoken = tk.Label(window3, text="Token", bg=background, fg=foreground)
            self.secret = tk.Entry(window3, text="Secret")
            labelsecret = tk.Label(window3, text="Secret", bg=background, fg=foreground)
            self.public_address = tk.Entry(window3, text="Public Address")
            labelpublic = tk.Label(window3, text="Public Address", bg=background, fg=foreground)
            self.button21 = tk.Button(window3, text="Add", command=self.update_setup)
            self.button21.grid(row=8, column=1)
            self.custodial = tk.Checkbutton(window3, text='Custodial', variable=self.var1, onvalue=1, offvalue=0,
                                            bg=background, fg=foreground)
            self.delegate = tk.Checkbutton(window3, text='Delegate', variable=self.var2, onvalue=1, offvalue=0,
                                           bg=background, fg=foreground)
            self.custodial.grid(row=2, column=1)
            self.network.grid(row=3, column=1)
            self.delegate.grid(row=4, column=1)
            self.public_address.grid(row=5, column=1)
            self.token.grid(row=6, column=1)
            self.name.grid(row=1, column=1)
            self.secret.grid(row=7, column=1)

            labelname.grid(row=1, column=0)
            labelnetwork.grid(row=3, column=0)
            labeltoken.grid(row=6, column=0)
            labelsecret.grid(row=7, column=0)
            labelpublic.grid(row=5, column=0)

        def update_setup(self):
            if self.name.get() == '':
                windownok = tk.Toplevel(bg=background)
                labnok = tk.Label(windownok, text="Name is a mandatory field", bg=background, fg=foreground)
                labnok.grid(row=1, column=1)
            else:
                tl.setup.append(dict({'name': self.name.get(), 'isCustodial': bool(self.var1.get()),
                                      'network': self.network.get(), "delegate": self.var2.get(), 'credentials': {
                        'token': self.token.get(), 'secret': self.secret.get()
                    }, 'PublicAddress': self.public_address.get()}))
                windowok = tk.Toplevel()
                labok = tk.Label(windowok, text=self.name.get() + " succesfully added to setup file",
                                 bg=background, fg=foreground)
                labok.grid(row=1, column=1)
            self.public_address.delete(0, tk.END)
            self.name.delete(0, tk.END)
            self.network.delete(0, tk.END)
            self.token.delete(0, tk.END)
            self.secret.delete(0, tk.END)
            self.var1.set(0)
            self.var2.set(0)
            with open(tl.wdir.replace("system", "") + "setup.json", "w") as handle21:
                json.dump(tl.setup, handle21)


    FirstUseWindow(main_window)
    main_window.mainloop()

else:
    # ------------------------------------------------------------ #
    #                   Start Tkinter window                       #
    # ------------------------------------------------------------ #

    # LOGO
    logo_Canvas = tk.Canvas(main_window, width=129, height=129)
    logo_Canvas.grid(row=0, column=0, rowspan=6, columnspan=6)
    logo = tk.PhotoImage(file=tl.wdir.replace("system", "images\\") + "logo.png").subsample(2, 2)
    logo_Canvas.create_image(0, 0, anchor=tk.NW, image=logo)

    # Total invested box
    total_invested_canvas = tk.Canvas(main_window, bg=background, height=canvas_height, width=190)
    total_invested_canvas.grid(row=0, column=11, columnspan=13, rowspan=6)

    # Update files button box
    update_canvas = tk.Canvas(main_window, bg=background, height=canvas_height, width=250)
    update_canvas.grid(row=0, column=24, columnspan=13, rowspan=6)

    # Synch Google drive button box
    gd_sync_canvas = tk.Canvas(main_window, bg=background, height=canvas_height, width=230)
    gd_sync_canvas.grid(row=0, column=37, columnspan=14, rowspan=6)

    # Graph box
    graphstyle = 'mike'  # 'charles'

    zero_data = pd.DataFrame(index=pd.date_range(dt.datetime.now() - dt.timedelta(days=7), dt.datetime.now(), freq="d"))
    zero_data['Open'] = [0] * len(zero_data.index)
    zero_data['High'] = [0] * len(zero_data.index)
    zero_data['Close'] = [0] * len(zero_data.index)
    zero_data['Low'] = [0] * len(zero_data.index)
    fig, axis = mpf.plot(  # mpf returns a tuple with figure and axis, the figure is passed to canvasTK
        data=zero_data,
        type='line',
        style=graphstyle,
        figsize=(7, 5),
        returnfig=True,
        addplot=mpf.make_addplot(data=zero_data, y_on_right=False, type='line')
    )
    fig.patch.set_facecolor('black')
    chart = FigureCanvasTkAgg(fig, main_window)
    chart.get_tk_widget().grid(row=9, column=12, columnspan=39, rowspan=31)

    # LABELS

    labplot = tk.Label(main_window, text="SELECT YOUR PLOT", bg=background, fg=foreground)
    labplot.grid(row=8, column=0, columnspan=8)

    labplot_account = tk.Label(main_window, text="Account", bg=background, fg=foreground)
    labplot_account.grid(row=10, column=8, sticky=tk.W, columnspan=3, rowspan=2)

    labplot_token = tk.Label(main_window, text="Token", bg=background, fg=foreground)
    labplot_token.grid(row=12, column=8, sticky=tk.W, columnspan=3, rowspan=2)

    labplot_granularity = tk.Label(main_window, text="Granularity", bg=background, fg=foreground)
    labplot_granularity.grid(row=14, column=8, sticky=tk.W, columnspan=3, rowspan=2)

    labplot_graph = tk.Label(main_window, text="Graph Type", bg=background, fg=foreground)
    labplot_graph.grid(row=16, column=8, sticky=tk.W, columnspan=3, rowspan=2)

    # ------------------------------------------------------------ #
    #                   Set up start from sysinfo                  #
    # ------------------------------------------------------------ #
    total = None
    history_file = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
    with open(tl.wdir + "\\sysinfo.json") as ol:
        sysinfo = json.load(ol)
    total_invested = sysinfo.get("totalinvested")

    conversion_rate = tl.get_currency_rate(sysinfo.get('currency').upper())

    if len(history_file) != 0:
        with open('chronology.pickle', 'rb') as handle:
            floaded = pk.load(handle)
        if floaded is not None and floaded.get('total').get('pltotale').shape[0] != 0:
            pl1 = floaded.get('total').get('pltotale').iloc[:, -1].sum(axis=0) * conversion_rate
            if total_invested > 0:
                mess3 = "PL(%): " + str(
                    round((pl1 - float(total_invested)) / float(total_invested) * 100, 2)) + "%" + " PL: " + str(
                    round(round(pl1, 2) -
                          float(total_invested), 2)) + " " + sysinfo.get('currency').upper() + " Total: " + str(
                    round(pl1, 2)) + " " + sysinfo.get('currency').upper()
        else:
            floaded = tl.create_new_balance_dict()
            with open(tl.wdir.replace("system", "") + 'chronology.pickle', 'wb') as handle1:
                pk.dump(floaded, handle1, protocol=pk.HIGHEST_PROTOCOL)
            pl1 = 0
            mess3 = "PL: No data yet"
    else:
        pl1 = 0
        mess3 = "PL: No data yet"


    class Start:
        def __init__(self, root):
            self.root = root

            self.button = tk.Button(root, text="Update balance", command=self.start)
            self.button.grid(row=2, column=27, columnspan=7, rowspan=2)

            self.buttonCurr = tk.Button(root, text="Update currency", command=self.update_currency)
            self.buttonCurr.grid(row=7, column=44, columnspan=5)

            self.last_update = sysinfo.get('lastupdate')
            self.label = tk.Label(root, text=f"Last updated on: {self.last_update}", bg=background, fg=foreground)
            self.label.grid(row=3, column=24, columnspan=13, rowspan=2)

            self.message = ''

            self.label2 = tk.Label(root, text=self.message, bg=background, fg=foreground)
            self.label2.grid(row=8, column=23, columnspan=11)

            self.message3 = mess3
            self.label3 = tk.Label(root, text=self.message3, bg=background, fg=foreground)
            self.label3.grid(row=7, column=23, columnspan=15)
            self.label3.config(width=40)

            self.currency = tk.StringVar(root, value=sysinfo.get('currency'))

            fiat = ["USD", "AUD", "BRL", "EUR", "GBP", "HKD", "NOK", "RUB", "TRY"]

            self.select = tk.OptionMenu(root, self.currency, sysinfo.get('currency'), *fiat)
            self.select.grid(row=7, column=39, columnspan=4)

        def start(self):
            global total, sysinfo, total_invested, conversion_rate
            if len(history_file) != 0:
                self.message = "Opening chronology"
                self.label2.config(text=self.message)
                self.root.update()
                with open('chronology.pickle', 'rb') as handle1:
                    floadedc = pk.load(handle1)

                try:
                    self.message = "Updating accounts"
                    self.label2.config(text=self.message)
                    self.root.update()
                    total = tl.get_balances(tl.setup, history_dict=floadedc)
                except ValueError:
                    self.message = "ERROR check execution.log"
                    self.label2.config(text=self.message)
                    self.root.update()
                    logging.error(
                        f"Error updating accounts, EthScanToken: {tl.etherscan_token}, BSCScanToken: {tl.bscscantoken}")
                    return "ERROR"

                self.message = "Saving results"
                self.label2.config(text=self.message)
                self.root.update()
                with open(tl.wdir.replace("system", "") + 'chronology.pickle', 'wb') as handle1:
                    pk.dump(total, handle1, protocol=pk.HIGHEST_PROTOCOL)

                self.message = "Data updated"
                self.label2.config(text=self.message)
                self.root.update()

                self.last_update = tl.datetime_to_str(dt.datetime.now())
                self.label.config(text=f"Last update: {self.last_update}")
                sysinfo['lastupdate'] = self.last_update
                sysinfo['currency'] = self.currency.get()

                with open(tl.wdir + '\\sysinfo.json', 'w') as outfile:
                    json.dump(sysinfo, outfile)
            else:
                try:
                    self.message = "Updating accounts"
                    self.label2.config(text=self.message)
                    self.root.update()
                    total = tl.get_balances(tl.setup, history_dict=None)
                except ValueError:
                    self.message = "ERROR check account info and/or Scan tokens"
                    self.label2.config(text=self.message)
                    self.root.update()
                    logging.error(
                        f"Error updating accounts, EthScanToken: {tl.etherscan_token}, BSCScanToken: {tl.bscscantoken}")
                    return "ERROR"

                self.message = "Saving results"
                self.label2.config(text=self.message)
                self.root.update()
                with open(tl.wdir.replace("system", "") + 'chronology.pickle', 'wb') as handle1:
                    pk.dump(total, handle1, protocol=pk.HIGHEST_PROTOCOL)

                self.message = "Data updated"
                self.label2.config(text=self.message)
                self.root.update()

                self.last_update = tl.datetime_to_str(dt.datetime.now())
                self.label.config(text=f"Last update: {self.last_update}")
                self.root.update()
                sysinfo['lastupdate'] = self.last_update
                sysinfo['currency'] = self.currency.get()

                with open(tl.wdir + '\\sysinfo.json', 'w') as outfile:
                    json.dump(sysinfo, outfile)

            pl1new = total.get('total').get('pltotale').iloc[:, -1].sum(axis=0)

            conversion_rate = tl.get_currency_rate(sysinfo.get('currency').upper())

            pl1new *= conversion_rate
            self.message3 = "PL(%): " + str(
                round((pl1new - float(total_invested)) / float(total_invested) * 100, 2)) + "%" + " PL: " + str(
                round(round(pl1new, 2) -
                      float(total_invested), 2)) + " " + sysinfo.get('currency').upper() + " Total: " + str(
                round(pl1new, 2)) + " " + sysinfo.get('currency').upper()
            self.label3.config(text=self.message3)
            self.root.update()

        def update_currency(self):
            global total_invested, conversion_rate, total, history_file

            sysinfo['currency'] = self.currency.get()

            with open(tl.wdir + '\\sysinfo.json', 'w') as outfile:
                json.dump(sysinfo, outfile)
            history_file = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
            if len(history_file) != 0:
                with open('chronology.pickle', 'rb') as handle1:
                    total = pk.load(handle1)
                pl1new = total.get('total').get('pltotale').iloc[:, -1].sum(axis=0)

                conversion_rate = tl.get_currency_rate(sysinfo.get('currency').upper())

                pl1new *= conversion_rate
                self.message3 = "PL(%): " + str(
                    round((pl1new - float(total_invested)) / float(total_invested) * 100, 2)) + "%" + " PL: " + str(
                    round(round(pl1new, 2) -
                          float(total_invested), 2)) + " " + sysinfo.get('currency').upper() + " Total: " + str(
                    round(pl1new, 2)) + " " + sysinfo.get('currency').upper()
                self.label3.config(text=self.message3)
                self.root.update()
            else:
                self.message3 = "PL: No data yet"
                self.label3.config(text=self.message3)
                self.root.update()


    class TotInvested:
        def __init__(self, root, totalinv):
            self.root = root
            self.total = totalinv
            self.label2 = tk.Label(text="Insert total amount invested", bg=background, fg=foreground)
            self.label2.grid(row=1, column=11, columnspan=13)
            self.entry = tk.Entry(main_window)
            self.entry.config(width=11)
            self.entry.grid(row=2, column=14, columnspan=4)
            self.entry.insert(0, str(self.total))
            self.update = sysinfo.get("totalinvestedupdate")
            self.button = tk.Button(main_window, text="Update", command=self.show_entry_fields)
            self.button.grid(row=2, column=19, columnspan=3)
            self.label = tk.Label(text=f'Last: {self.update}', bg=background, fg=foreground)
            self.label.grid(row=3, column=11, columnspan=13)  # .grid(row=4, column=13, columnspan=13, rowspan=2)

        def show_entry_fields(self):
            global total_invested, sysinfo
            total_invested = self.entry.get()
            sysinfo['totalinvested'] = float(total_invested)
            sysinfo['totalinvestedupdate'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(tl.wdir + '\\sysinfo.json', 'w') as outfile:
                json.dump(sysinfo, outfile)
            self.label.config(text=self.update)
            self.root.update()


    class NewWindowUpdateSetup:
        def __init__(self, root):
            self.root = root
            self.button = tk.Button(main_window, text="Update setup files", command=self.new_window)
            self.button.grid(row=1, column=27, columnspan=7, rowspan=2)

            self.token = tk.StringVar()

            self.location = tk.StringVar(value="Select location")
            self.locationlist = [p['name'] for p in tl.setup]
            self.ignorecsv = pd.read_csv(tl.wdir + "\\ignore.csv")
            self.toremove = [f'{a}, {b}' for a, b in
                             zip(self.ignorecsv['Token'].tolist(), self.ignorecsv['Location'].tolist())]
            self.toremoveval = tk.StringVar(value="Select entry to remove")

        def new_window(self):
            window22 = tk.Toplevel(bg=background)
            lab = tk.Label(window22, text="Update setup files", bg=background, fg=foreground)
            accountinfo = tk.Button(window22, text="Update accounts information", command=self.update_accounts)
            ignore = tk.Button(window22, text="Update tokens to ignore", command=self.update_ignore)
            staking = tk.Button(window22, text="Update Binance staking information", command=self.update_staking,
                                state=tk.DISABLED)
            lab.grid(row=0, column=0)
            accountinfo.grid(row=1, column=0)
            ignore.grid(row=2, column=0)
            staking.grid(row=3, column=0)

        def update_ignore(self):
            ignorewindow = tk.Toplevel(bg=background)

            label1 = tk.Label(ignorewindow, text="Insert token and location to ignore:", bg=background, fg=foreground)
            label1.grid(columnspan=6, column=1, row=1)

            label2 = tk.Label(ignorewindow, text="ADD", bg=background, fg=foreground)
            label2.grid(rowspan=2, column=0, row=2)

            label3 = tk.Label(ignorewindow, text="REMOVE", bg=background, fg=foreground)
            label3.grid(column=0, row=8)

            label4 = tk.Label(ignorewindow, text="Select token to remove from ignore:", bg=background, fg=foreground)
            label4.grid(columnspan=6, column=1, row=7)

            label5 = tk.Label(ignorewindow, text="Token", bg=background, fg=foreground)
            label5.grid(column=1, row=2)

            label6 = tk.Label(ignorewindow, text="Location", bg=background, fg=foreground)
            label6.grid(column=1, row=3)

            # TODO: update removelist names
            self.tokentoignore = tk.Entry(ignorewindow, textvariable=self.token)
            self.tokentoignore.grid(columnspan=3, column=2, row=2)

            self.locationtoignore = tk.OptionMenu(ignorewindow, self.location, *self.locationlist)
            self.locationtoignore.grid(columnspan=3, column=2, row=3)

            self.toremoveoptions = tk.OptionMenu(ignorewindow, self.toremoveval, *self.toremove)
            self.toremoveoptions.grid(columnspan=3, column=1, row=8)

            buttonmod = tk.Button(ignorewindow, text='Add', command=self.add_to_csv)
            buttonmod.grid(column=3, row=4)

            buttonmod2 = tk.Button(ignorewindow, text='Remove', command=self.remove_from_csv)
            buttonmod2.grid(column=2, row=9)

        def remove_from_csv(self):
            index = [i for i, x in enumerate(self.toremove) if x == self.toremoveval.get()]
            self.ignorecsv.drop(index, axis=0, inplace=True)
            self.toremoveval.set(value="Select entry to remove")
            self.ignorecsv.reset_index(inplace=True, drop=True)
            self.ignorecsv.to_csv(tl.wdir + "\\ignore.csv", index=False)
            self.toremove = [f'{a}, {b}' for a, b in
                             zip(self.ignorecsv['Token'].tolist(), self.ignorecsv['Location'].tolist())]
            self.toremoveoptions['menu'].delete(0, 'end')

            # Insert list of new options (tk._setit hooks them up to var)
            new_choices = self.toremove
            for choice in new_choices:
                self.toremoveoptions['menu'].add_command(label=choice, command=tk._setit(self.toremoveval, choice))

        def add_to_csv(self):
            stringtoappend = pd.DataFrame({'Token': [self.token.get()], 'Location': [self.location.get()]})
            ignorecsv = pd.read_csv(tl.wdir + "\\ignore.csv")
            ignorecsv = ignorecsv.append(stringtoappend)
            ignorecsv.reset_index(inplace=True, drop=True)
            ignorecsv.to_csv(tl.wdir + "\\ignore.csv", index=False)
            self.location.set(value="Select location")
            self.ignorecsv = ignorecsv

            self.tokentoignore.delete(0, tk.END)
            self.root.update()

            confirmwindow = tk.Toplevel(self.root)
            glab = tk.Label(confirmwindow,
                            text=f'{self.token.get()} in {self.location.get()} correctly added to the ignore file')
            glab.pack()

        def update_accounts(self):
            window2 = tk.Toplevel()
            self.add = tk.Button(window2, text="Add element", command=self.add)
            self.remove = tk.Button(window2, text="Remove element", command=self.remove)
            self.add.grid(row=1, column=1)
            self.remove.grid(row=1, column=2)
            self.label_tot = tk.Label(window2,
                                      text="Accounts included in setup.json: " + ", ".join(
                                          [i.get('name') for i in tl.setup]))
            self.label_tot.grid(row=2, column=1)

        def add(self):
            window3 = tk.Toplevel()
            self.var1 = tk.IntVar()
            self.var2 = tk.IntVar()
            self.name = tk.Entry(window3, text="Name")
            labelname = tk.Label(window3, text="Account Name")
            self.network = tk.Entry(window3, text="Network")
            labelnetwork = tk.Label(window3, text="Network")
            self.token = tk.Entry(window3, text="Token")
            labeltoken = tk.Label(window3, text="Token")
            self.secret = tk.Entry(window3, text="Secret")
            labelsecret = tk.Label(window3, text="Secret")
            self.public_address = tk.Entry(window3, text="Public Address")
            labelpublic = tk.Label(window3, text="Public Address")
            self.button21 = tk.Button(window3, text="Add", command=self.update_setup)
            self.button21.grid(row=8, column=1)
            self.custodial = tk.Checkbutton(window3, text='Custodial', variable=self.var1, onvalue=1, offvalue=0)
            self.delegate = tk.Checkbutton(window3, text='Delegate', variable=self.var2, onvalue=1, offvalue=0)
            self.custodial.grid(row=2, column=1)
            self.network.grid(row=3, column=1)
            self.delegate.grid(row=4, column=1)
            self.public_address.grid(row=5, column=1)
            self.token.grid(row=6, column=1)
            self.name.grid(row=1, column=1)
            self.secret.grid(row=7, column=1)

            labelname.grid(row=1, column=0)
            labelnetwork.grid(row=3, column=0)
            labeltoken.grid(row=6, column=0)
            labelsecret.grid(row=7, column=0)
            labelpublic.grid(row=5, column=0)

        def update_setup(self):
            if self.name.get() == '':
                windownok = tk.Toplevel()
                labnok = tk.Label(windownok, text="Name is a mandatory field")
                labnok.grid(row=1, column=1)
            else:
                tl.setup.append(dict({'name': self.name.get(), 'isCustodial': bool(self.var1.get()),
                                      'network': self.network.get(), "delegate": self.var2.get(), 'credentials': {
                        'token': self.token.get(), 'secret': self.secret.get()
                    }, 'PublicAddress': self.public_address.get()}))
                windowok = tk.Toplevel()
                labok = tk.Label(windowok, text=self.name.get() + " succesfully added to setup file")
                labok.grid(row=1, column=1)
            self.public_address.delete(0, tk.END)
            self.name.delete(0, tk.END)
            self.network.delete(0, tk.END)
            self.token.delete(0, tk.END)
            self.secret.delete(0, tk.END)
            self.var1.set(0)
            self.var2.set(0)
            with open(tl.wdir.replace("system", "") + "setup.json", "w") as handle21:
                json.dump(tl.setup, handle21)
            self.label_tot.config(
                text="Accounts included in setup.json: " + ", ".join([i.get('name') for i in tl.setup]))

        def remove(self):
            self.window4 = tk.Toplevel()
            self.removename = tk.StringVar(self.window4, value="Select account to remove")
            self.listtemp = [t.get('name') for t in tl.setup]
            self.removedropdown = tk.OptionMenu(self.window4, self.removename,
                                                *self.listtemp)
            self.removebutt = tk.Button(self.window4, text="Remove", command=self.pop_from_list)
            self.removedropdown.grid(row=1, column=1)
            self.removebutt.grid(row=2, column=1)

        def pop_from_list(self):
            temp = [p.get('name') for p in tl.setup]
            pos = [tl.setup[x] for x, y in enumerate(temp) if y != self.removename.get()]
            removed = [tl.setup[x] for x, y in enumerate(temp) if y == self.removename.get()]
            if self.removename.get() == "Select account to remove":
                winderror = tk.Toplevel()
                labok = tk.Label(winderror, text="Please make a selection")
                labok.grid(row=1, column=1)
            else:
                if len(removed) > 0:
                    windowok = tk.Toplevel()
                    labok = tk.Label(windowok, text=self.removename.get() + " succesfully removed from setup file")
                    labok.grid(row=1, column=1)
                else:
                    windownok = tk.Toplevel()
                    labnok = tk.Label(windownok, text=self.removename.get() + " could not be found in the setup file")
                    labnok.grid(row=1, column=1)
                self.removename = tk.StringVar(self.window4, value="Select account to remove")
                self.listtemp = [p.get('name') for p in pos]
                self.removedropdown['menu'].delete(0, tk.END)
                self.removedropdown = tk.OptionMenu(self.window4, self.removename,
                                                    *self.listtemp)
                self.removedropdown.grid(row=1, column=1)
            tl.setup = pos
            with open(tl.wdir.replace("system", "") + "setup.json", "w") as handle:
                json.dump(pos, handle)
            self.label_tot.config(
                text="Accounts included in setup.json: " + ", ".join([i.get('name') for i in tl.setup]))

        @staticmethod
        def update_staking():
            windowsta = tk.Toplevel()
            lab = tk.Label(windowsta, text="COMING SOON! PLease for now modify the file binancestaking.csv manually")
            lab.pack()


    class SyncGD:
        def __init__(self, root):
            self.root = root
            self.button = tk.Button(self.root, text="Sync with Google Drive", command=self.backup_google_drive)
            self.button.grid(row=2, column=40, columnspan=9)
            self.lastsynch = "Last synced: " + sysinfo.get('GDlastupdate')
            self.labelsynch = tk.Label(self.root, text=self.lastsynch, bg=background, fg=foreground)
            self.labelsynch.grid(row=3, column=39, columnspan=11)

        def backup_google_drive(self):
            global sysinfo
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
            drive = GoogleDrive(gauth)
            # If the folder does not exist create it
            gdfolder = utiltools.check_drive_folder(namef="trackerPython", drive=drive)
            # Get file names and modification time
            gdfile = [x for x in drive.ListFile({'q': f"'{gdfolder}' in parents and trashed=false"}).GetList()]
            gdfilenames = [gdfile[x].get('title') for x in range(len(gdfile))]
            gdfileids = [gdfile[x].get('id') for x in range(len(gdfile))]
            gdmodified = [dt.datetime.strptime(gdfile[x].get('modifiedDate').split(".")[0], "%Y-%m-%dT%H:%M:%S")
                              .replace(tzinfo=timezone.utc).astimezone(tz=None).timestamp() for x in range(len(gdfile))]

            # Get names of files to sync
            locfilestosync = [f for f in os.listdir(tl.wdir) if "cryptohistory" in f]
            locfilestosync.extend(['binancestaking.csv', 'ignore.csv', 'othertoken.csv', 'scantokens.csv'])
            locfilestosyncinroot = ['chronology.pickle', 'setup.json']

            indsysinfo = [x for x, y in enumerate(gdfilenames) if y == 'sysinfo.json']

            if len(indsysinfo) > 0:
                locmodified = os.path.getmtime(tl.wdir + "\\" + 'sysinfo.json')
                if gdmodified[indsysinfo[0]] > locmodified:
                    fileDownloaded = drive.CreateFile({'id': gdfileids[indsysinfo[0]], 'parents': [{"id": gdfolder}]})
                    fileDownloaded.GetContentFile(tl.wdir + "\\sysinfo.json")
                    with open(tl.wdir + "\\sysinfo.json") as ol1:
                        sysinfo = json.load(ol1)
                    self.lastsynch = "Last synced " + sysinfo.get('GDlastupdate')
                    self.labelsynch.config(text=self.lastsynch)
                    self.root.update()

            for file in locfilestosync:
                locmodified = os.path.getmtime(tl.wdir + "\\" + file)
                ind = [x for x, y in enumerate(gdfilenames) if file == y]
                self.lastsynch = "Syncing " + file
                self.labelsynch.config(text=self.lastsynch)
                self.root.update()
                if len(ind) > 0:
                    if gdmodified[ind[0]] > locmodified:
                        fileDownloaded = drive.CreateFile({'id': gdfileids[ind[0]], 'parents': [{"id": gdfolder}]})
                        fileDownloaded.GetContentFile(tl.wdir + "\\" + gdfilenames[ind[0]])
                    else:
                        fileUpload = drive.CreateFile({'id': gdfileids[ind[0]], 'parents': [{"id": gdfolder}]})
                        fileUpload.SetContentFile(tl.wdir + "\\" + gdfilenames[ind[0]])
                        fileUpload.Upload()
                else:
                    fileUpload = drive.CreateFile({'title': file, 'parents': [{"id": gdfolder}]})
                    fileUpload.SetContentFile(tl.wdir + "\\" + file)
                    fileUpload.Upload()

            for file in locfilestosyncinroot:
                locmodified = os.path.getmtime(tl.wdir.replace("system", "") + file)
                ind = [x for x, y in enumerate(gdfilenames) if file == y]
                self.lastsynch = "Syncing " + file
                self.labelsynch.config(text=self.lastsynch)
                self.root.update()
                if len(ind) > 0:
                    if gdmodified[ind[0]] > locmodified:
                        fileDownloaded = drive.CreateFile({'id': gdfileids[ind[0]], 'parents': [{"id": gdfolder}]})
                        fileDownloaded.GetContentFile(tl.wdir.replace("system", "") + gdfilenames[ind[0]])
                    else:
                        fileUpload = drive.CreateFile({'id': gdfileids[ind[0]], 'parents': [{"id": gdfolder}]})
                        fileUpload.SetContentFile(tl.wdir.replace("system", "") + gdfilenames[ind[0]])
                        fileUpload.Upload()
                else:
                    fileUpload = drive.CreateFile({'title': file, 'parents': [{"id": gdfolder}]})
                    fileUpload.SetContentFile(tl.wdir.replace("system", "") + file)
                    fileUpload.Upload()

            self.lastsynch = "Last synced: " + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sysinfo['GDlastupdate'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(tl.wdir + '\\sysinfo.json', 'w') as outfile:
                json.dump(sysinfo, outfile)
            self.labelsynch.config(text=self.lastsynch)
            self.root.update()

            if len(indsysinfo) > 0:
                fileUpload = drive.CreateFile({'id': gdfileids[indsysinfo[0]], 'parents': [{"id": gdfolder}]})
                fileUpload.SetContentFile(tl.wdir + "\\" + 'sysinfo.json')
                fileUpload.Upload()
            else:
                fileUpload = drive.CreateFile({'title': 'sysinfo.json', 'parents': [{"id": gdfolder}]})
                fileUpload.SetContentFile(tl.wdir + "\\" + 'sysinfo.json')
                fileUpload.Upload()


    class Graph:
        def __init__(self, root):
            self.root = root
            histfileplot = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
            if len(histfileplot) != 0:
                with open('chronology.pickle', 'rb') as histplot:
                    self.data = pk.load(histplot)
                self.availability = tk.ACTIVE
                self.tokenlist = list(self.data['total']['totalbalance'].index)
                self.tokenlist.insert(0, 'Total balance')
                self.accountlist = list(self.data['byAccount'].keys())
                self.accountlist.insert(0, 'Total balance')
            else:
                self.availability = tk.DISABLED
                self.tokenlist = ['No data available']
                self.accountlist = ['No data available']

            self.button = tk.Button(self.root, text="Plot", command=self.plot_values, state=self.availability)
            self.button.grid(row=21, column=0, columnspan=8)

            self.buttonup = tk.Button(self.root, text="Update data", command=self.update_widget)
            self.buttonup.grid(row=14, column=51, columnspan=5, rowspan=2)

            self.buttonup = tk.Button(self.root, text="Reset selections", command=self.reset)
            self.buttonup.grid(row=19, column=0, columnspan=8, rowspan=2)

            self.token = tk.StringVar(value=self.tokenlist[0])
            self.account = tk.StringVar(value=self.accountlist[0])

            self.selecttoken = tk.OptionMenu(root, self.token, *self.tokenlist)
            self.selecttoken.config(width=12, anchor=tk.W)
            self.selecttoken.grid(row=12, column=0, columnspan=8, rowspan=2)

            self.selectaccount = tk.OptionMenu(root, self.account, *self.accountlist)
            self.selectaccount.config(width=12, anchor=tk.W)
            self.selectaccount.grid(row=10, column=0, columnspan=8, rowspan=2)

            self.gran = {'Hourly': '1H', '4 Hours': '4H', '12 Hours': '12H', 'Daily': '1D', 'Weekly': '7D',
                         'Monthly': '1M', 'Yearly': '1Y'}
            self.granularity = tk.StringVar(value='Daily')
            self.selectgran = tk.OptionMenu(root, self.granularity, *list(self.gran.keys()))
            self.selectgran.config(width=12)
            self.selectgran.grid(row=14, column=0, columnspan=8, rowspan=2)

            self.graphtype = tk.StringVar(value='candle')
            self.typelist = ['candle', 'line']
            self.selecttype = tk.OptionMenu(root, self.graphtype, *self.typelist)
            self.selecttype.config(width=12)
            self.selecttype.grid(row=16, column=0, columnspan=8, rowspan=2)

        def reset(self):
            self.token.set(value=self.tokenlist[0])
            self.account.set(value=self.accountlist[0])
            self.granularity.set(value='Daily')
            self.graphtype.set(value='candle')

        def update_widget(self):
            histfileplot = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
            if len(histfileplot) != 0:
                with open('chronology.pickle', 'rb') as histplot:
                    self.data = pk.load(histplot)
                self.availability = tk.ACTIVE
            else:
                self.availability = tk.DISABLED
            self.root.update()

        def plot_values(self, exchangerate=conversion_rate, datapointstoplot=60):
            # Everytime user clicks on plot the history is updated
            histfileplot = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
            # So is currency
            currency = sysinfo.get('currency')

            if len(histfileplot) != 0:
                with open('chronology.pickle', 'rb') as histplot:
                    data = pk.load(histplot)

            token = self.token.get()
            if token == 'Total balance':
                token = None

            account = self.account.get()
            if account == 'Total balance':
                account = None

            granularity = self.gran[self.granularity.get()]
            graphtype = self.graphtype.get()

            if account is None and token is None:
                for key in ['open', 'close', 'high', 'low']:
                    if isinstance(data['total'][key], pd.Series):
                        data['total'][key] = pd.DataFrame(data['total'][key])
                datatoplot = pd.DataFrame()
                datatoplot['Date'] = [dt.datetime.fromtimestamp(int(x)) for x in list(data['total']['open'].index)]
                datatoplot.index = datatoplot['Date']
                datatoplot.drop(['Date'], axis=1, inplace=True)
                datatoplot['Open'] = data['total']['open'].iloc[:, -1].tolist()
                datatoplot['High'] = data['total']['high'].iloc[:, -1].tolist()
                datatoplot['Low'] = data['total']['low'].iloc[:, -1].tolist()
                datatoplot['Close'] = data['total']['close'].iloc[:, -1].tolist()

                datatomerge = pd.DataFrame(index=pd.date_range(datatoplot.index[0], datatoplot.index[-1], freq="h"),
                                           data=[0] * len(
                                               pd.date_range(datatoplot.index[0], datatoplot.index[-1], freq="h")
                                           ), columns=["todrop"])
                finalplot = datatoplot.join(datatomerge, how='outer')
                finalplot.drop(['todrop'], axis=1, inplace=True)
                finalplot.ffill(inplace=True)
                finalplot.bfill(inplace=True)

                finalplot = finalplot[finalplot.index <= tl.datetime_to_str(dt.datetime.now())]

                datafin = finalplot.resample(granularity.upper()).mean() * exchangerate
                if datafin.shape[0] > datapointstoplot:
                    datafin = datafin.tail(datapointstoplot)
                if graphtype == 'candle':
                    opt = mpf.make_addplot(data=datafin, y_on_right=False, type='candle')
                else:
                    opt = None
                fig, axis = mpf.plot(  # mpf returns a tuple with figure and axis, the figure is passed to canvasTK
                    data=datafin,
                    type=graphtype,
                    style=graphstyle,
                    title='Total',
                    ylabel=f'Total Amount ({currency})',
                    hlines=dict(hlines=[datafin['Close'].tolist()[-1]], linestyle='-.'),
                    mav=(10, 25),
                    figsize=(7, 5),
                    returnfig=True,
                    addplot=opt
                )
                # fig.patch.set_facecolor('black')
                chart = FigureCanvasTkAgg(fig, self.root)
                # chart.draw()
                chart.get_tk_widget().grid(row=9, column=12, columnspan=39, rowspan=31)
            elif account is not None and token is None:
                for key in ['open', 'close', 'high', 'low']:
                    if isinstance(data['byAccount'][account][key], pd.Series):
                        data['byAccount'][account][key] = pd.DataFrame(data['byAccount'][account][key])
                    if 0 in data['byAccount'][account][key].index:
                        data['byAccount'][account][key].drop(0, axis=0, inplace=True)
                datatoplot = pd.DataFrame()
                datatoplot['Date'] = [dt.datetime.fromtimestamp(int(x)) for x in
                                      list(data['byAccount'][account]['open'].index)]
                datatoplot.index = datatoplot['Date']
                datatoplot.drop(['Date'], axis=1, inplace=True)
                datatoplot['Open'] = data['byAccount'][account]['open'].sum(axis=1).tolist()
                datatoplot['High'] = data['byAccount'][account]['high'].sum(axis=1).tolist()
                datatoplot['Low'] = data['byAccount'][account]['low'].sum(axis=1).tolist()
                datatoplot['Close'] = data['byAccount'][account]['close'].sum(axis=1).tolist()

                datatomerge = pd.DataFrame(index=pd.date_range(datatoplot.index[0], datatoplot.index[-1], freq="h"),
                                           data=[0] * len(
                                               pd.date_range(datatoplot.index[0], datatoplot.index[-1], freq="h")
                                           ), columns=["todrop"])
                finalplot = datatoplot.join(datatomerge, how='outer')
                finalplot.drop(['todrop'], axis=1, inplace=True)
                finalplot.ffill(inplace=True)
                finalplot.bfill(inplace=True)

                datafin = finalplot.resample(granularity.upper()).mean() * exchangerate
                if datafin.shape[0] > datapointstoplot:
                    datafin = datafin.tail(datapointstoplot)
                fig, axis = mpf.plot(  # mpf returns a tuple with figure and axis, the figure is passed to canvasTK
                    data=datafin,
                    type=graphtype,
                    style=graphstyle,
                    title=f'Total amount in {account}',
                    ylabel=f'Total amount in {account} ({currency})',
                    hlines=dict(hlines=[datafin['Close'].tolist()[-1]], linestyle='-.'),
                    returnfig=True
                )
                chart = FigureCanvasTkAgg(fig, self.root)
                chart.draw()
                chart.get_tk_widget().grid(row=9, column=12, columnspan=39, rowspan=31)

            elif account is None and token is not None:
                dftemp = pd.DataFrame()
                for account in data['byAccount'].keys():
                    for key in ['open', 'close', 'high', 'low']:
                        if isinstance(data['byAccount'][account][key], pd.Series):
                            data['byAccount'][account][key] = pd.DataFrame(data['byAccount'][account][key])
                        if 0 in data['byAccount'][account][key].index:
                            data['byAccount'][account][key].drop(0, axis=0, inplace=True)
                        if token in data['byAccount'][account][key].columns:
                            if dftemp.shape[1] == 0:
                                dftemp = pd.DataFrame(data['byAccount'][account][key][token])
                            else:
                                dftemp = dftemp.join(data['byAccount'][account][key][token])
                                dftemp = dftemp[~dftemp.index.duplicated(keep='first')]
                            if dftemp.shape[1] == 1:
                                dftemp.columns = [key]
                            else:
                                cols = list(dftemp.columns)
                                cols[-1] = key
                                dftemp.columns = cols

                dftemp.bfill(inplace=True)
                dftemp.ffill(inplace=True)

                datatoplot = pd.DataFrame()
                datatoplot['Date'] = [dt.datetime.fromtimestamp(int(x)) for x in list(dftemp.index)]
                datatoplot.index = datatoplot['Date']
                datatoplot.drop(['Date'], axis=1, inplace=True)
                datatoplot['Open'] = pd.DataFrame(dftemp['open']).sum(axis=1).tolist()
                datatoplot['High'] = pd.DataFrame(dftemp['high']).sum(axis=1).tolist()
                datatoplot['Low'] = pd.DataFrame(dftemp['low']).sum(axis=1).tolist()
                datatoplot['Close'] = pd.DataFrame(dftemp['close']).sum(axis=1).tolist()

                datafin = datatoplot.resample(granularity.upper()).mean() * exchangerate
                datafin.ffill(inplace=True)
                datafin.bfill(inplace=True)

                if datafin.shape[0] > datapointstoplot:
                    datafin = datafin.tail(datapointstoplot)
                fig, axis = mpf.plot(  # mpf returns a tuple with figure and axis, the figure is passed to canvasTK
                    data=datafin,
                    type=graphtype,
                    title=f'Total {token}',
                    style=graphstyle,
                    ylabel=f'Total {token} ({currency})',
                    hlines=dict(hlines=[datafin['Close'].tolist()[-1]], linestyle='-.'),
                    returnfig=True
                )
                chart = FigureCanvasTkAgg(fig, self.root)
                chart.draw()
                chart.get_tk_widget().grid(row=9, column=12, columnspan=39, rowspan=31)

            elif account is not None and token is not None:
                inaccount = True
                for key in ['open', 'close', 'high', 'low']:
                    if isinstance(data['byAccount'][account][key], pd.Series):
                        data['byAccount'][account][key] = pd.DataFrame(data['byAccount'][account][key])
                    if 0 in data['byAccount'][account][key].index:
                        data['byAccount'][account][key].drop(0, axis=0, inplace=True)
                    if token not in data['byAccount'][account][key].columns:
                        inaccount = False
                        window4 = tk.Toplevel()
                        warning = tk.Label(window4, text=f'ERROR: {token} not present in account {account}')
                        warning.pack()
                        break
                if inaccount:
                    datatoplot = pd.DataFrame()
                    datatoplot['Date'] = [dt.datetime.fromtimestamp(int(x)) for x in
                                          list(data['byAccount'][account]['open'].index)]
                    datatoplot.index = datatoplot['Date']
                    datatoplot.drop(['Date'], axis=1, inplace=True)
                    datatoplot['Open'] = pd.DataFrame(data['byAccount'][account]['open'][token]).sum(axis=1).tolist()
                    datatoplot['High'] = pd.DataFrame(data['byAccount'][account]['high'][token]).sum(axis=1).tolist()
                    datatoplot['Low'] = pd.DataFrame(data['byAccount'][account]['low'][token]).sum(axis=1).tolist()
                    datatoplot['Close'] = pd.DataFrame(data['byAccount'][account]['close'][token]).sum(axis=1).tolist()

                    datafin = datatoplot.resample(granularity.upper()).mean() * exchangerate
                    datafin.ffill(inplace=True)
                    datafin.bfill(inplace=True)

                    if datafin.shape[0] > datapointstoplot:
                        datafin = datafin.tail(datapointstoplot)
                    fig, axis = mpf.plot(  # mpf returns a tuple with figure and axis, the figure is passed to canvasTK
                        data=datafin,
                        style=graphstyle,
                        type=graphtype,
                        title=f'{token} in {account}',
                        ylabel=f'{token} in {account} ({currency})',
                        hlines=dict(hlines=[datafin['Close'].tolist()[-1]], linestyle='-.'),
                        returnfig=True
                    )
                    chart = FigureCanvasTkAgg(fig, self.root)
                    chart.draw()
                    chart.get_tk_widget().grid(row=9, column=12, columnspan=39, rowspan=31)


    class DeleteDate:
        def __init__(self, root):
            self.root = root
            self.button = tk.Button(self.root, text="Delete last entry", command=self.delete_last_confirm)
            self.button.grid(row=10, column=51, columnspan=5, rowspan=2)

        def delete_last_confirm(self):
            window1 = tk.Toplevel(bg=background)

            def closewindow():
                window1.destroy()

            labconfirm = tk.Label(window1, text='Are you sure you want to delete last date? '
                                                'This action cannot be undone', bg=background, fg=foreground)
            labconfirm.grid(row=0, column=0, columnspan=3)
            buttonyes = tk.Button(window1, text='YES', command=self.delete_last_date)
            buttonyes.config(width=20)
            buttonyes.grid(row=1, column=0)
            buttonno = tk.Button(window1, text='NO', command=closewindow)
            buttonno.config(width=20)
            buttonno.grid(row=1, column=2)

        def delete_last_date(self):
            histfile1 = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
            self.window155 = tk.Toplevel()
            self.message = tk.Label(self.window155, text="")
            self.message.pack()

            if len(histfile1) > 0:
                global sysinfo
                with open('chronology.pickle', 'rb') as han:
                    floadedd = pk.load(han)
                if len(floadedd.get('total').get('pltotale').columns) != 1:
                    lastdate = floadedd.get('total').get('pltotale').columns[-1]
                    pendate = floadedd.get('total').get('pltotale').columns[-2]

                    sysinfo['lastupdate'] = tl.datetime_to_str(dt.datetime.fromtimestamp(pendate))
                    with open(tl.wdir + "\\sysinfo.json", "w") as ol1:
                        json.dump(sysinfo, ol1)

                    for key1 in floadedd.get('byAccount').keys():
                        for key2 in floadedd['byAccount'][key1].keys():
                            if isinstance(floadedd['byAccount'][key1][key2], dict):
                                for key3 in floadedd['byAccount'][key1][key2].keys():
                                    if lastdate == 0:
                                        floadedd['byAccount'][key1][key2][key3] = pd.DataFrame()
                                    else:
                                        floadedd['byAccount'][key1][key2][key3].drop(
                                            floadedd['byAccount'][key1][key2][key3].index[
                                                np.logical_and(
                                                    floadedd['byAccount'][key1][key2][
                                                        key3].index <= lastdate,
                                                    floadedd['byAccount'][key1][key2][
                                                        key3].index > pendate)], axis=0,
                                            inplace=True)
                            else:
                                if lastdate == 0:
                                    floadedd['byAccount'][key1][key2] = pd.DataFrame()
                                else:
                                    if key2 == 'balance':
                                        floadedd['byAccount'][key1][key2].drop(lastdate, axis=1, inplace=True)
                                    else:
                                        floadedd['byAccount'][key1][key2].drop(floadedd['byAccount'][key1][key2].index[
                                                                                   np.logical_and(
                                                                                       floadedd['byAccount'][key1][
                                                                                           key2].index <= lastdate,
                                                                                       floadedd['byAccount'][key1][
                                                                                           key2].index > pendate)],
                                                                               axis=0,
                                                                               inplace=True)
                    for key1 in floadedd['total'].keys():
                        if lastdate == 0:
                            floadedd['total'][key1] = pd.DataFrame()
                        else:
                            if key1 in ['close', 'open', 'high', 'low']:
                                floadedd['total'][key1].drop(floadedd['total'][key1].index[np.logical_and(
                                    floadedd['total'][key1].index <= lastdate,
                                    floadedd['total'][key1].index > pendate)],
                                                             axis=0,
                                                             inplace=True)
                            else:
                                floadedd['total'][key1].drop(lastdate, axis=1, inplace=True)
                    with open(tl.wdir.replace("system", "") + 'chronology.pickle', 'wb') as handle1:
                        pk.dump(floadedd, handle1, protocol=pk.HIGHEST_PROTOCOL)
                else:
                    os.remove("chronology.pickle")

                    sysinfo['lastupdate'] = "No data yet"
                    with open(tl.wdir + "\\sysinfo.json", "w") as ol1:
                        json.dump(sysinfo, ol1)

                self.message.config(
                    text="Last date was removed from history, please restart the program to update all data",
                    bg=background,
                    fg=foreground)
                self.root.update()
            else:
                self.message.config(
                    text="No data available yet")
                self.root.update()


    def delete_history():
        histfileg = [x for x in os.listdir(tl.wdir.replace("system", "")) if x == "chronology.pickle"]
        if len(histfileg) != 0:
            os.remove(tl.wdir.replace('system', histfileg[0]))
            wind = tk.Toplevel()
            lab = tk.Label(wind, text="History succesfully removed", bg=background, fg=foreground)
            lab.pack()
        else:
            wind = tk.Toplevel()
            lab = tk.Label(wind, text="No history found", bg=background, fg=foreground)
            lab.pack()


    def delete_confirm():
        window1 = tk.Toplevel(bg=background)

        def closewindow():
            window1.destroy()

        labconfirm = tk.Label(window1, text='Are you sure you want to delete all your history? '
                                            'This action cannot be undone', bg=background, fg=foreground)
        labconfirm.grid(row=0, column=0, columnspan=3)
        buttonyes = tk.Button(window1, text='YES', command=delete_history)
        buttonyes.config(width=20)
        buttonyes.grid(row=1, column=0)
        buttonno = tk.Button(window1, text='NO', command=closewindow)
        buttonno.config(width=20)
        buttonno.grid(row=1, column=2)


    deletebutton1 = tk.Button(main_window, text="Delete history", command=delete_confirm)
    deletebutton1.grid(row=12, column=51, columnspan=5, rowspan=2)

    deletebutton = tk.Button(main_window, text="Restart APP", command=restart)
    deletebutton.grid(row=16, column=51, columnspan=5, rowspan=2)

    # Start main loop

    Graph(main_window)
    NewWindowUpdateSetup(main_window)
    TotInvested(main_window, total_invested)
    Start(main_window)
    SyncGD(main_window)
    DeleteDate(main_window)
    main_window.mainloop()
