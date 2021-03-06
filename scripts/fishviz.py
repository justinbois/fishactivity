#!/usr/bin/env python

import argparse

import numpy as np
import pandas as pd

import bokeh.io

import fishact
import tsplot


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate interactive plots of zebrafish activity time series.')
    parser.add_argument('activity_fname', metavar='activity_file', type=str,
                        help='Name of activity file.')
    parser.add_argument('gtype_fname', metavar='genotype_file', type=str,
                        help='Name of genotype file.')
    parser.add_argument('--out', '-o', action='store', default=None,
                        dest='html_file',
                        help='Name of file to store output. Defaults to the prefix of the activity file name + `.html`.')
    parser.add_argument('--browser', '-b', action='store', default=None,
                        dest='browser',
                        help='Which browser to use for displaying plots.')
    parser.add_argument('--sleep', '-z', action='store_true', dest='sleep',
                        help='Select to plot minutes of sleep over time.')
    parser.add_argument('--summary', '-s', action='store_true', dest='summary',
                    help='Select to give summary plot, not plot of all fish.')
    parser.add_argument('--svg', '-g', action='store_true', dest='svg',
                    help='Save traces as SVG as well as HTML.')
    parser.add_argument('--confint', '-c', action='store', dest='confint',
                        default='95',
                        help='Confidence interval for summary plot; default is 95. If 0, no confidence interval shows.')
    parser.add_argument('--window', '-w', action='store', dest='ind_win',
                        default=10,
                help='Number of time points to use in averages (default 10)')
    parser.add_argument('--lightson', '-l', action='store', dest='lights_on',
                        default='9:00:00',
                help='Time that lights come on, e.g., 9:00:00 (default)')
    parser.add_argument('--lightsoff', '-d', action='store',
                          dest='lights_off', default='23:00:00',
                help='Time that lights go off, e.g., 23:00:00 (default)')
    parser.add_argument('--startday', '-D', action='store',
                        dest='day_in_the_life', default=4,
            help="Day in zebrafish's life that experiment began (default 5)" )
    parser.add_argument('--stat', '-S', action='store',
                        dest='summary_trace', default='mean',
                        help="Which summary statistic to compute, choose from [mean, median, max, min, none], default is mean.")
    parser.add_argument('--timeshift', '-t', action='store',
                        dest='time_shift', default='center',
                        help="Which part of time interval is used in plot; acceptable values: [left, right, center, interval], default is left.")
    parser.add_argument('--ignoregtype', '-i', action='store_true',
                        dest='ignore_gtype', default=False,
                        help="Ignore genotype information (genotype file still must be provided to determine which fish are analyze-able).")
    args = parser.parse_args()

    # Specify output
    if args.html_file is not None:
        outfile = args.html_file
    else:
        outfile = args.activity_fname[:args.activity_fname.rfind('.')] + '.html'
    bokeh.io.output_file(outfile, title='fish sleep explorer')

    # Set the confidence interval
    ptiles = (2.5, 97.5)
    confint = True
    if args.confint == '0':
        confint = False
    else:
        conf_size = float(args.confint)
        ptiles = (50-conf_size/2, 50+conf_size/2)

    # What to plot
    if args.sleep:
        signal = 'sleep'
    else:
        signal = 'activity'

    # Parse data Frames
    print('Loading in the data....')
    df = fishact.parse.load_activity(
                 args.activity_fname, args.gtype_fname, args.lights_on,
                 args.lights_off, int(args.day_in_the_life))

    # Resample the data
    df = fishact.parse.resample(df, int(args.ind_win))

    # Get summary statistic
    if args.summary_trace in ['none', 'None']:
        args.summary_trace = None

    # Make plots
    if args.ignore_gtype:
        if args.summary:
            df['genotype'] = ['all combined'] * len(df)
            p = fishact.visualize.summary(
                    df, signal=signal, summary_trace=args.summary_trace,
                    time_shift=args.time_shift, confint=confint, ptiles=ptiles,
                    legend=False)
        else:
            p = fishact.visualize.all_traces(df, signal=signal,
                summary_trace=args.summary_trace, time_shift=args.time_shift)
    else:
        if args.summary:
            p = fishact.visualize.summary(
                    df, signal=signal, summary_trace=args.summary_trace,
                    time_shift=args.time_shift, confint=confint, ptiles=ptiles)
        else:
            p = fishact.visualize.grid(
                    df, signal=signal, summary_trace=args.summary_trace,
                    time_shift=args.time_shift)

    if args.svg:
        if bokeh.__version__ < '0.12.6':
            print('\n')
            print('Must have Bokeh version 0.12.6 or greater to output SVG.')
            print('Not exporting SVG.\n')
        else:
            # Get filename for SVGs
            if outfile[-5:] == '.html':
                fname = outfile[:-5] + '.svg'
            else:
                fname = outfile + '.svg'

            # Export them
            try:
                # Set SVG as backend
                p.output_backend = 'svg'

                print(bokeh.io.export_svgs(p, filename=fname))

                # Set backend back to canvas
                p.output_backend = 'canvas'
            except:
                print('\nUnable to export SVG.\n')

    # Save and show HTML file
    bokeh.io.save(p)
    bokeh.io.show(p, browser=args.browser)
