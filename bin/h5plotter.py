#!/usr/bin/env python3

import matplotlib
import h5py
import sys
import pylab as plt
import os
import numpy as np
import glob
from tqdm import *
from multiprocessing import Pool
import scipy.signal as s
from subprocess import check_output
from dm_utils import get_dm
from matplotlib import gridspec
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
matplotlib.use('Agg')


def plot_h5(h5_file, show=False, save=True, detrend=True, dm_range_scale=1.0):
    """
    Plot the h5 candidate file
    :param h5_file: Address of the candidate h5 file
    :param show: Argument to display the plot
    :param save: Argument to save the plot
    :param detrend: Optional argument to detrend the frequency-time array
    :param dm_range_scale: Optional scaling factor to limit the dm-range in the plot.
    :return:
    """
    try:
        plt.clf()
        fig = plt.figure(figsize=(15, 8))
        with h5py.File(h5_file, 'r') as f:
            to_print = []
            for key in f.attrs.keys():
                to_print.append(f'{key} : {f.attrs[key]}\n')
            src = f.attrs['source_name']#.decode("utf-8")
            try:
                expected_dm = get_dm(src)
            except:
                print(f'did not get expected_dm from get_dm')
            to_print.append(f'expected DM : {expected_dm}\n')
            str_print = ''.join(to_print)
            dm_time = np.array(f['data_dm_time'])
            if detrend:
                freq_time = s.detrend(np.array(f['data_freq_time'])[:, ::-1].T)
            else:
                freq_time = np.array(f['data_freq_time'])[:, ::-1].T
            dm_time[dm_time != dm_time] = 0
            freq_time[freq_time != freq_time] = 0
            freq_time -= np.median(freq_time)
            freq_time /= np.std(freq_time)
            nt, nf = freq_time.shape
            gs = gridspec.GridSpec(3, 2, width_ratios=[4, 1], height_ratios=[1, 1, 1])
            ax1 = plt.subplot(gs[0, 0])
            ax2 = plt.subplot(gs[1, 0])
            ax3 = plt.subplot(gs[2, 0])
            ax4 = plt.subplot(gs[:, 1])
            fch1, foff, nchan, dm, cand_id, tsamp, dm_opt, snr, snr_opt, width = f.attrs['fch1'], \
                                                                                 f.attrs['foff'], f.attrs['nchans'], \
                                                                                 f.attrs['dm'], f.attrs['cand_id'], \
                                                                                 f.attrs['tsamp'], f.attrs['dm_opt'], \
                                                                                 f.attrs['snr'], f.attrs['snr_opt'], \
                                                                                 f.attrs['width']
            if width > 1:
                ts = np.linspace(-128,128,256) * tsamp * width*1000 / 2
            else:
                ts = np.linspace(-128,128,256) * tsamp* 1000

            # make the bins square
            ax1.plot(ts, freq_time.sum(0), color='k', drawstyle='steps-mid')

            # Also fix that the time series is aligned on the x-axis with dynamic spectrum and DMT plot
            ax1.set_xlim(ts[0], ts[-1])

            ax1.set_ylabel('Flux (Arb. Units)')

            # plot dynamic spectrum
            ax2.imshow(freq_time, aspect='auto', extent=[ts[0], ts[-1], fch1, fch1 + (nchan * foff)], interpolation='none')
            ax2.set_ylabel('Frequency (MHz)')

            dmt_extent = [ts[0], ts[-1], dm + dm * dm_range_scale, dm - dm * dm_range_scale]

            ax3.imshow(dm_time, aspect='auto', extent=dmt_extent, interpolation='none')
            ax3.set_ylabel(r'DM (pc cm$^{-3}$)')
            ax3.set_xlabel('Time (ms)')
            ax4.text(0.2, 0, str_print, fontsize=14, ha='left', va='bottom', wrap=True)
            ax4.axis('off')
            plt.tight_layout()
            if save:
                plt.savefig(h5_file[:-3] + '.png', bbox_inches='tight')
            if show:
                plt.show()
            else:
                plt.close()
            return h5_file[:-3] + '.png'
    except ValueError:
        return None


if __name__ == '__main__':
    with Pool(processes=4) as p:
        args = glob.glob(sys.argv[1])
        max_ = len(args)
        with tqdm(total=max_) as pbar:
            for i, _ in tqdm(enumerate(p.imap_unordered(plot_h5, args, chunksize=2))):
                pbar.update()
