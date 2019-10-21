# edited 10/04/19 by fr293 to clear out old code and make readable
# BEAD 40um, viscosity 1000 cSt
import numpy as np
import os
import scipy.signal
from math import *
import csv
# this import statement is used, do not remove it
from mpl_toolkits.mplot3d import axis3d
import matplotlib.pyplot as plt
import math

# can introduce several flags to select only some classes of trajectory
spim_box_big = 'TRUE'
show_plots = 'FALSE'
path_file = 'D:\\sync_folder\\calibration\\'
name = 'noam_0A1_181019_mod.csv'


# convert inputs to floats. If inputs are not numbers, then leave them unchanged
def conv_f(elem_in):
    try:
        elem_out = float(elem_in)
    except ValueError:
        elem_out = elem_in

    return elem_out


# conversion of cvs list in a list of lists
def conv_csv(data_in, no_elem_per_line):
    data_out = []
    for ii in range(no_elem_per_line):
        data_out.append([])
    for jj in range(1, len(data_in)):
        temp = data_in[jj].rstrip('\n').split(',')
        for ii in range(no_elem_per_line):
            data_out[ii].append(conv_f(temp[ii]))
    return data_out


# conversion of a list in sublist fct of condition // IN: pos of param & condition
def conv_to_sublist(data_in, cond, index_col):
    data_out = []
    for ii in range(len(data_in)):
        data_out.append([])
    for jj in range(len(data_in[index_col])):
        if data_in[index_col][jj] == cond:
            for ii in range(len(data_in)):
                data_out[ii].append(data_in[ii][jj])
    return data_out


# detect number of distinct trajectories looking at jumps in time record
# considering as relevant only the trajectories longer than a given number of seconds
def traject_detection(data_in):
    if len(data_in[0]) != 0:
        #time_bet_jumps = 1.5
        #no_pct_traj = 15
        #fr293 edit to increase time
        time_bet_jumps = 5
        no_pct_traj = 50

        traject = 1
        index_traject = []
        # fr293 altered to remove superfluous lines
        # index_traject_s_e = []
        # index_traject_s_e.append(0)
        index_traject_s_e = [0]
        time_old = data_in[0][0]

        for ii in range(1, len(data_in[0])):
            time_new = data_in[0][ii]
            if (time_new - time_old) > time_bet_jumps:
                traject = traject + 1
                index_traject_s_e.append(ii - 1)
                index_traject.append(index_traject_s_e)
                # fr293 altered to remove superfluous lines
                # index_traject_s_e = []
                # index_traject_s_e.append(ii)
                index_traject_s_e = [ii]

            time_old = time_new

        index_traject_s_e.append(ii)
        index_traject.append(index_traject_s_e)
        index_traject_new = []

        for jj in range(traject):
            max_index = index_traject[jj][1]
            min_index = index_traject[jj][0]
            # do not consider short trajectories
            if (max_index - min_index) > no_pct_traj:
                index_traject_new.append(index_traject[jj])

        erase_traject = len(index_traject) - len(index_traject_new)
    else:
        index_traject_new = []
        erase_traject = 0

    return index_traject_new, erase_traject


# calculate z refined by focus parameter
def z_correct_foc(ff1, ff2, zz_in):
    nn_oil = 1.403

    x11 = 7.60268
    x22 = 7.64864
    y11 = 1.38048
    y22 = 0.71469

    slope = (y11 - y22) / (x11 - x22)
    inters = y11 - slope * x11
    f_1_over_f_2 = ff1 / ff2

    z_actual_arb = (f_1_over_f_2 - inters) / slope
    z_desired_arb = (1.1 - inters) / slope
    delta_z_oil = z_actual_arb - z_desired_arb
    delta_z_air = delta_z_oil * 1000.0 * nn_oil

    zz_out = zz_in + delta_z_air
    return zz_out


# smoothing z coordinates with a filter. Start with degree 3 and 1/4 of points as window
def filter_z_sg(input_xx, input_yy):
    win_len = int(float(len(input_yy)) / 4.0)
    if win_len % 2 == 0:
        win_len = win_len + 1
    print win_len
    out_yy = scipy.signal.savgol_filter(np.array(input_yy), win_len, 3, mode='nearest')
    print out_yy
    out_xx = input_xx
    # as python list - to convert
    return out_xx, out_yy.tolist()


# extract data to fit and prepare for fitting
def extract_data_to_fit(data_in, min_max, coord):
    if coord == 'x':
        index_jj = 2
    elif coord == 'y':
        index_jj = 3
    elif coord == 'z':
        index_jj = 5
    else:
        print 'error'

    xx = []
    yy = []
    tt = []

    for ii in range(min_max[0], min_max[1]):
        # time not treated
        xx.append(data_in[0][ii])
        if index_jj == 5:
            z_temp = data_in[index_jj][ii]
            # focus_1
            foc_1 = data_in[6][ii]
            # focus_2
            foc_2 = data_in[7][ii]
            z_foc = z_correct_foc(foc_1, foc_2, z_temp)
            yy.append(z_foc)
        else:
            # x,y or z
            yy.append(data_in[index_jj][ii])

        # temperature
        tt.append(data_in[10][ii] - (0.27132 * data_in[10][ii] - 5.545 - 0.4))
    return np.array(xx), np.array(yy), np.array(tt)


# calculate the quality of fit
def eval_r_square(data_xx, data_yy, coef_pol, rss):
    yy_average = np.sum(data_yy) / len(data_yy)
    sst = np.sum((data_yy - yy_average) ** 2)
    deg_pol = len(coef_pol) - 1
    n_tot = len(data_yy)

    r__2 = 1 - rss / sst
    r__2__adj = r__2 - (1 - r__2) * deg_pol / (n_tot - deg_pol - 1)

    return r__2__adj


# detect the degree of fitting polynomial
def remove_1st_two_points(function_input):  # now are 5 points removed
    output = np.delete(function_input, [0, 6])
    return output


# detect the degree of fitting polynomial
def quality_control_fit(input_xx_1, input_yy_1, coord_fit_1):
    rsquare = []
    if coord_fit_1 == 'x' or coord_fit_1 == 'y':
        if abs(input_yy_1[0] - input_yy_1[len(input_yy_1) - 1]) < 6.0:
            best_pol_deg = 1
            fit_quality = 'Y'
        else:
            for pol_deg in range(1, 5):
                coef, rss, _, _, _ = np.polyfit(input_xx_1, input_yy_1, pol_deg, full=True)
                # in case that the interpolation fails
                if len(rss) == 0:
                    r_square_adj = 0
                else:
                    r_square_adj = eval_r_square(input_xx_1, input_yy_1, coef, rss[0])
                rsquare.append(r_square_adj)
            max_val = rsquare[0]
            best_pol_deg = 1
            for pp in range(1, len(rsquare)):
                if rsquare[pp] > max_val:
                    max_val = rsquare[pp]
                    best_pol_deg = pp + 1
            if rsquare[best_pol_deg - 1] > 0.9995:
                fit_quality = 'Y'
            else:
                fit_quality = 'N'

    elif coord_fit_1 == 'z':
        for pol_deg in range(1, 2):  # only linear for z axis
            coef, rss, _, _, _ = np.polyfit(input_xx_1, input_yy_1, pol_deg, full=True)
            if len(rss) == 0:
                r_square_adj = 0
            else:
                r_square_adj = eval_r_square(input_xx_1, input_yy_1, coef, rss[0])
            rsquare.append(r_square_adj)
        max_val = rsquare[0]
        best_pol_deg = 1

        for pp in range(1, len(rsquare)):
            if rsquare[pp] > max_val:
                max_val = rsquare[pp]
                best_pol_deg = pp + 1

        if rsquare[best_pol_deg - 1] > 0.90:
            fit_quality = 'Y'
        else:
            fit_quality = 'N'

    else:
        print 'error 2'

    # print best_pol_deg, fit_quality
    return best_pol_deg, fit_quality


# adding coefficient based exponents after derivation
def correcting_coef(input_coef):
    output_coef = np.delete(input_coef, [len(input_coef) - 1])
    for jj in range(len(output_coef)):
        output_coef[jj] = (len(output_coef) - jj) * output_coef[jj]
    return output_coef


# calculate force from velocity
def veloc_to_force(in_veloc, in_tt, coord_fit):
    # round error - modify numbers
    # t_ref = 25.0
    rho_oil_25 = 970.0
    rho_oil_0 = 992.0

    # 10^-6 m^2/s
    # fr293 edit for lower viscosity oil sample
    visc_c_25 = 350
    #visc_c_25 = 1025.164
    const = 1683.0

    # Kg.m^3
    rho_bead = 1500.0

    # micrometers
    diam_bead = 41.13
    acc_g = 9.81

    out_force = np.zeros(len(in_veloc))

    if coord_fit == 'x' or coord_fit == 'y':
        for kk in range(len(in_veloc)):
            visc_c = visc_c_25 * exp(const * (1.0 / (273.0 + in_tt[kk]) - 1.0 / 298.0))
            rho_oil = rho_oil_0 + in_tt[kk] * (rho_oil_25 - rho_oil_0) / 25.0
            # divided by 1000 to eliminate calculus with big numbers
            visc = visc_c * rho_oil / 1000.0
            # 10^(-15) N / 10^6 # nN
            out_force[kk] = 6.0 * np.pi * in_veloc[kk] * visc * diam_bead / 2.0 / 1000000.0
            #  10^(-6) m/ s * 10^(-6) m * 10^(-6) m^2/s kg/m3 *10^(-3)
    elif coord_fit == 'z':
        # 10^-15 m3
        vol = np.pi / 6.0 * (diam_bead / 10.0) ** 3
        # 10^-12 kg
        mass = vol * (rho_bead / 1000.0)
        # 10^-9 N or nN
        weight = mass * acc_g / 1000.0
        for kk in range(len(in_veloc)):
            visc_c = visc_c_25 * exp(const * (1.0 / (273.0 + in_tt[kk]) - 1.0 / 298.0))
            rho_oil = rho_oil_0 + in_tt[kk] * (rho_oil_25 - rho_oil_0) / 25.0
            # divided by 1000 to eliminate calculus with big numbers
            visc = visc_c * rho_oil / 1000.0
            # 10^(-15) N # nN
            f_stokes = -6.0 * np.pi * in_veloc[kk] * visc * diam_bead / 2.0 / 1000000.0
            # in nN
            f_buoy = - vol * acc_g * rho_oil / 1000000.0
            f_mag = -weight - f_stokes - f_buoy
            # print weight, f_stokes, f_buoy, f_mag,in_veloc[kk]
            out_force[kk] = f_mag

    return out_force


# fit polynomials and select the most efficient
def best_fited_curve(input_xx, input_yy, input_tt, axa_fit):
    pol_deg_end, fit_qual = quality_control_fit(input_xx, input_yy, axa_fit)
    coef_coord = np.polyfit(input_xx, input_yy, pol_deg_end)
    fct_coord = np.poly1d(coef_coord)
    coord_fit = fct_coord(input_xx)
    coef_veloc = correcting_coef(coef_coord)
    fct_veloc = np.poly1d(coef_veloc)
    veloc_fit = fct_veloc(input_xx)
    qual_fit = [fit_qual] * len(coord_fit)
    force_fit = veloc_to_force(veloc_fit, input_tt, axa_fit)

    return coord_fit.tolist(), force_fit.tolist(), veloc_fit.tolist(), qual_fit


# plot trajectories and the best fit
def evaluate_fit_graph(axa_x, axa_y_1, axa_y_2, coord, index, i_conf):
    if show_plots == 'TRUE':
        plt.plot(axa_x, axa_y_1, 'ro', axa_x, axa_y_2, 'g-')
        plt.ylabel(coord + ' (um)', fontsize=14)
        plt.title('Force    ' + i_conf + '   axis    ' + coord.upper() + '    ['
                  + str(index).strip('[]') + ']', fontsize=18, color='blue')
        plt.xlabel('Time (s)', fontsize=14)
        plt.show()
        plt.close('all')
    return


# fit trajectories with polynomials
def fit_traject(data_in, index_in, i_comb):

    # x,y,z, fx,fy,fz,  vx,vy,vz, Qtx,Qty, Qtz
    data_out = [[] for x in xrange(12)]
    # range_x = [0, 3, 6, 9]
    # range_y = [1, 4, 7, 10]
    # range_z = [2, 5, 8, 11]
    select_coord = 'x'
    for kk in range(len(index_in)):
        select_traj = kk
        val_x, val_y, val_t = extract_data_to_fit(data_in, index_in[select_traj], select_coord)
        val_x = remove_1st_two_points(val_x)
        val_y = remove_1st_two_points(val_y)
        val_t = remove_1st_two_points(val_t)

        out_1, out_2, out_3, out_4 = best_fited_curve(val_x, val_y, val_t, select_coord)
        evaluate_fit_graph(val_x, val_y, np.array(out_1), select_coord, index_in[select_traj], i_comb)
        data_out[0] = data_out[0] + out_1
        data_out[3] = data_out[3] + out_2
        data_out[6] = data_out[6] + out_3
        data_out[9] = data_out[9] + out_4

    select_coord = 'y'

    for kk in range(len(index_in)):
        select_traj = kk
        val_x, val_y, val_t = extract_data_to_fit(data_in, index_in[select_traj], select_coord)
        val_x = remove_1st_two_points(val_x)
        val_y = remove_1st_two_points(val_y)
        val_t = remove_1st_two_points(val_t)

        out_1, out_2, out_3, out_4 = best_fited_curve(val_x, val_y, val_t, select_coord)
        evaluate_fit_graph(val_x, val_y, np.array(out_1), select_coord, index_in[select_traj], i_comb)
        data_out[1] = data_out[1] + out_1
        data_out[4] = data_out[4] + out_2
        data_out[7] = data_out[7] + out_3
        data_out[10] = data_out[10] + out_4

    select_coord = 'z'

    for kk in range(len(index_in)):
        select_traj = kk
        val_x, val_y, val_t = extract_data_to_fit(data_in, index_in[select_traj], select_coord)
        val_x = remove_1st_two_points(val_x)
        val_y = remove_1st_two_points(val_y)
        val_t = remove_1st_two_points(val_t)

        out_1, out_2, out_3, out_4 = best_fited_curve(val_x, val_y, val_t, select_coord)
        evaluate_fit_graph(val_x, val_y, np.array(out_1), select_coord, index_in[select_traj], i_comb)
        data_out[2] = data_out[2] + out_1
        data_out[5] = data_out[5] + out_2
        data_out[8] = data_out[8] + out_3
        data_out[11] = data_out[11] + out_4

    return data_out


# transpose a list
def transp(data_in):
    fdata_out = [list(i) for i in zip(*data_in)]
    return fdata_out


# calculate total force (nN)
def add_total_force(data_in):
    # print 'size', len(data_in)

    for ii in range(len(data_in)):
        f_tot = math.sqrt(math.pow(data_in[ii][3], 2) + math.pow(data_in[ii][4], 2) + math.pow(data_in[ii][5], 2))
        temp = list(data_in[ii])
        temp.append(f_tot)
        data_in[ii] = tuple(temp)

    return data_in


# save results to files
def save_to_file(results, full_path, str_config):
    data_transp_old = transp(results)
    data_transp = add_total_force(data_transp_old)
    full_path_new = full_path[:-4] + '_I_config_' + str_config + '.csv'

    file_link = open(full_path_new, 'wb')
    header = 'x(um), y(um), z(um), fx(nN), fy(nN), fz(nN), vx(um/s), vy(um/s), vz(um/s), Qtx, Qty,Qtz, F(nN)' + '\n'
    file_link.writelines(header)
    writer = csv.writer(file_link, delimiter=',', lineterminator='\n')
    writer.writerows(data_transp)
    file_link.close()
    return


# save results on files after removing data outside of SPIM box (BIG box filter)
def remove_d_box(data_in):

    data_out = [[] for x in xrange(12)]  # x,y,z, fx,fy,fz,  vx,vy,vz, Qtx,Qty, Qtz

    for ii in range(len(data_in[0])):
        xx = data_in[0][ii]
        yy = data_in[1][ii]
        zz = data_in[2][ii]
        xxs, yys, zzs = coord_trans_invers(xx, yy, zz)
        if (abs(xxs) <= 226.0) and (abs(yys) <= 226.0) and (abs(zzs) <= 70.0):
            for jj in range(len(data_in)):
                data_out[jj].append(data_in[jj][ii])

    return data_out


# coordinates transformation between spim box (x'') to lab coordinate (x)
def coord_trans(xin, yin, zin):
    theta = 45.0 * np.pi / 180.0
    xout_ = xin * np.cos(theta) - zin * np.sin(theta)
    yout_ = yin
    zout_ = xin * np.sin(theta) + zin * np.cos(theta)
    xout = xout_ + 100.0
    yout = yout_
    zout = zout_ - 100.0
    return xout, yout, zout


# coordinates transformation between lab coordinates (x) to spim box (x'')
def coord_trans_invers(xin, yin, zin):
    theta = -45.0 * np.pi / 180.0
    xout_ = xin - 100.0
    yout_ = yin
    zout_ = zin + 100.0
    xout = xout_ * np.cos(theta) - zout_ * np.sin(theta)
    yout = yout_
    zout = xout_ * np.sin(theta) + zout_ * np.cos(theta)
    return xout, yout, zout


# generate the coordinates for the box to be plotted
def spim_box_ccordinates():
    data_out_final = []
    data_out = []
    data_x = []
    data_y = []
    data_z = []

    x, y, z = coord_trans(-226, 226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, 226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, -226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, -226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, 226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    data_out.append(data_x)
    data_out.append(data_y)
    data_out.append(data_z)

    data_out_final.append(data_out)

    data_out = []
    data_x = []
    data_y = []
    data_z = []

    x, y, z = coord_trans(-226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, -226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, -226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    data_out.append(data_x)
    data_out.append(data_y)
    data_out.append(data_z)

    data_out_final.append(data_out)

    data_out = []
    data_x = []
    data_y = []
    data_z = []

    x, y, z = coord_trans(-226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, -226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, -226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, 226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(-226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    data_out.append(data_x)
    data_out.append(data_y)
    data_out.append(data_z)

    data_out_final.append(data_out)

    data_out = []
    data_x = []
    data_y = []
    data_z = []

    x, y, z = coord_trans(226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, -226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, -226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, 226, 50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    x, y, z = coord_trans(226, 226, -50)
    data_x.append(x)
    data_y.append(y)
    data_z.append(z)

    data_out.append(data_x)
    data_out.append(data_y)
    data_out.append(data_z)

    data_out_final.append(data_out)

    return data_out_final


# plot final data
def plot_results(results_in):
    print 'plotting', len(results_in)

    # box_plot = spim_box_ccordinates()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(results_in[0], results_in[1], results_in[2], c='r', marker='*')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.view_init(elev=-153., azim=-126.)

    plt.show()
    plt.close('all')

    return


# plot forces total data
def plot_forces(data_in, title):
    temp = []

    # box_plot = spim_box_ccordinates()

    for kk in range(len(data_in[0])):
        temp.append(math.sqrt(math.pow(data_in[3][kk], 2) + math.pow(data_in[4][kk], 2) + math.pow(data_in[5][kk], 2)))

    fig = plt.figure(figsize=(10, 10))
    fig.suptitle('Configuration: ' + title, fontsize=20)

    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(data_in[0], temp, 'ro')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Force/nN')

    ax2 = fig.add_subplot(2, 2, 2)
    ax2.plot(data_in[1], temp, 'ro')
    ax2.set_xlabel('Y')
    ax2.set_ylabel('Force/nN')

    ax3 = fig.add_subplot(2, 2, 3)
    ax3.plot(data_in[2], temp, 'ro')
    ax3.set_xlabel('Z')
    ax3.set_ylabel('Force/nN')

    ax4 = fig.add_subplot(224, projection='3d')
    ax4.scatter(data_in[0], data_in[1], data_in[2], c='r', marker='*')
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    ax4.set_zlabel('Z')
    # to verify
    ax4.view_init(elev=-153., azim=-126.)

    plt.show()
    plt.close('all')
    return


def traj_to_force():
    # the number of elements is important
    no_elem_line = 19
    # this gives the exepected input format of the training data
    # t(sec), t_cor(sec), xb(um), yb(um), zb_oil(um), zb_air(um), focus1, focus2,temp(C), temp2(C), temp3(C),
    # I1(A), I2(A), I3(A), I4(A), PWS(ON/OFF),config(1-6/7), spim_box_small(Y/N), spim_box_big(Y/N) 3.643

    path_file_input = path_file + name

    ffile = open(path_file_input, 'r')
    fdata = ffile.readlines()
    # working data
    wdata = conv_csv(fdata, no_elem_line)
    # PWS is ON
    pdata = conv_to_sublist(wdata, 'True', 15)
    if spim_box_big == 'TRUE':
        # spim box data // small box = 15
        sdata = conv_to_sublist(pdata, 'YES', 18)
    else:
        sdata = conv_to_sublist(pdata, 'YES', 17)
    cdata_6 = conv_to_sublist(sdata, 6, 16)

    sdata = pdata
    cdata_1 = conv_to_sublist(sdata, 1, 16)
    cdata_2 = conv_to_sublist(sdata, 2, 16)
    cdata_3 = conv_to_sublist(sdata, 3, 16)
    cdata_4 = conv_to_sublist(sdata, 4, 16)
    cdata_5 = conv_to_sublist(sdata, 5, 16)

    index_traj_c1, reject_c1 = traject_detection(cdata_1)
    index_traj_c2, reject_c2 = traject_detection(cdata_2)
    index_traj_c3, reject_c3 = traject_detection(cdata_3)
    index_traj_c4, reject_c4 = traject_detection(cdata_4)
    index_traj_c5, reject_c5 = traject_detection(cdata_5)
    index_traj_c6, reject_c6 = traject_detection(cdata_6)

    print('Calculating forces from trajectory data')
    print 'West; ' + 'successful trajectiories ', str(len(index_traj_c1)), ' rejected trajectiories ' + str(reject_c1)
    print 'South; ' + 'successful trajectiories ', str(len(index_traj_c2)), ' rejected trajectiories ' + str(reject_c2)
    print 'North; ' + 'successful trajectiories ', str(len(index_traj_c3)), ' rejected trajectiories ' + str(reject_c3)
    print 'East; ' + 'successful trajectiories ', str(len(index_traj_c4)), ' rejected trajectiories ' + str(reject_c4)
    print 'Down; ' + 'successful trajectiories ', str(len(index_traj_c5)), ' rejected trajectiories ' + str(reject_c5)
    print 'Up; ' + 'successful trajectiories ', str(len(index_traj_c6)), ' rejected trajectiories ' + str(reject_c6)

    fdata_out_c1 = fit_traject(cdata_1, index_traj_c1, 'West')
    fdata_out_c2 = fit_traject(cdata_2, index_traj_c2, 'South')
    fdata_out_c3 = fit_traject(cdata_3, index_traj_c3, 'North')
    fdata_out_c4 = fit_traject(cdata_4, index_traj_c4, 'East')
    fdata_out_c5 = fit_traject(cdata_5, index_traj_c5, 'Down')
    fdata_out_c6 = fit_traject(cdata_6, index_traj_c6, 'Up')

    # comment because we take all data even is are outside of small box. Useful during fitting
    # if spim_box_big =='TRUE':
    #    fdata_out_c1 = remove_d_box(fdata_out_c1)
    #    fdata_out_c2 = remove_d_box(fdata_out_c2)
    #    fdata_out_c3 = remove_d_box(fdata_out_c3)
    #    fdata_out_c4 = remove_d_box(fdata_out_c4)

    # these lines plot the forces in 3d only
    # plot_results(fdata_out_c1)
    # plot_results(fdata_out_c2)
    # plot_results(fdata_out_c3)
    # plot_results(fdata_out_c4)
    # plot_results(fdata_out_c5)
    # plot_results(fdata_out_c6)

    save_to_file(fdata_out_c1, path_file_input, '1')
    save_to_file(fdata_out_c2, path_file_input, '2')
    save_to_file(fdata_out_c3, path_file_input, '3')
    save_to_file(fdata_out_c4, path_file_input, '4')
    save_to_file(fdata_out_c5, path_file_input, '5')
    save_to_file(fdata_out_c6, path_file_input, '6')

    plot_forces(fdata_out_c1, 'West')
    plot_forces(fdata_out_c2, 'South')
    plot_forces(fdata_out_c3, 'North')
    plot_forces(fdata_out_c4, 'East')
    plot_forces(fdata_out_c5, 'Down')
    plot_forces(fdata_out_c6, 'Up')

    print "finished calculating force data"
    return


def multiple_calibration(output_path):
    inputdata = np.loadtxt(output_path + '/starting_positions.csv', dtype=str, delimiter=',', skiprows=1)

    return


if __name__ == '__main__':

    traj_to_force()
