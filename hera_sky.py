"""
hera_sky.py
-----------

Nicholas Kern
"""
from flask import Flask, make_response
from flask import request
from flask import render_template

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from vis_sim import Sky_Model, Beam_Model
import numpy as np
from astropy.time import Time
import time
import aipy
import ephem
import StringIO
import base64

app = Flask(__name__)

def make_image(jd=None, nu=None):
    # initialize hera position
    AntArr = aipy.cal.get_aa('hsa7458_v001', np.array([0.15]))
    loc = ephem.Observer()
    loc.lon = AntArr.lon
    loc.lat = AntArr.lat

    # initialize sky models
    S = Sky_Model('pygsm_sky_models.npz', onepol=False)

    # get image parameters
    if jd is None:
        date = loc.date.datetime()
        jd = Time(loc.date.datetime()).jd
    else:
        date = Time(jd, format='jd').datetime
        loc.date = date

    if nu is None:
        nu = 150.0
        i = np.argmin(np.abs(S.sky_freqs - nu))
    else:
        i = np.argmin(np.abs(S.sky_freqs - nu))

    # get local time
    utc_date = '-'.join(map(str, date.utctimetuple()[:3]))
    utc_time = ':'.join(map(lambda x: "%02d"%x, date.utctimetuple()[3:6]))
    utc = utc_date + ' ' + utc_time

    # get image name
    img = StringIO.StringIO()

    # plot figure
    fig = plt.figure(figsize=(5,5))
    ax = fig.add_subplot(111)
    S.plot_sky(loc, S.sky_models[0, 0, i], ax=ax, cbar=False)
    ax.set_title("{} MHz\nLST {:.2f} hours\nJD {:.4f}\nUTC {}".format(S.sky_freqs[i], loc.sidereal_time()*12/np.pi, jd, utc))
    plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
    plt.close()

    # return image
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue())
    return plot_url

@app.route("/")
def main():
    plot_url = make_image()
    return render_template("index.html", plot_url=plot_url, footer_text="")

@app.route("/", methods=['POST'])
def main_post():
    try:
        jd = float(request.form['jd'])
        plot_url = make_image(jd=jd)
        footer_text = ""
    except:
        plot_url = make_image()
        footer_text = "That wasn't a float. Try again."
    return render_template("index.html", plot_url=plot_url, footer_text=footer_text)

if __name__ == "__main__":
    app.run()

