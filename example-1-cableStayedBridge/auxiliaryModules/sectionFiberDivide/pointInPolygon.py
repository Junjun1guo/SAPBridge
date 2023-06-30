#-*-coding: UTF-8-*-
######################################################################################
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#  Date: 05/02/2020
######################################################################################
######################################################################################
import numpy as np
import math
######################################################################################
def is_in_2d_polygon(point, vertices):
    """determine whether the point in the closed curved lines composed of vertices"""
    px = point[0]
    py = point[1]
    angle_sum = 0

    size = len(vertices)
    if size < 3:
        raise ValueError("len of vertices < 3")
    j = size - 1
    for i in range(0, size):
        sx = vertices[i][0]
        sy = vertices[i][1]
        tx = vertices[j][0]
        ty = vertices[j][1]
        #determine whether the node in a line based on the distance from the node to the line
        # y = kx + b, -y + kx + b = 0
        k = (sy - ty) / (sx - tx + 0.000000000001)  # avoid divide zero
        b = sy - k * sx
        dis = np.abs(k * px - 1 * py + b) / np.sqrt(k * k + 1)
        if dis < 0.000001:  #the node in the line
            if sx <= px <= tx or tx <= px <= sx:  #the node in the line
                return True
        #calculate the angle
        angle = math.atan2(sy - py, sx - px) - math.atan2(ty - py, tx - px)
        #the angle shoule with [-pi,pi]
        if angle >= math.pi:
            angle = angle - math.pi * 2
        elif angle <= -math.pi:
            angle = angle + math.pi * 2
        #cumulation
        angle_sum += angle
        j = i
    #calculate the diffrence between the sum angles and 2pi with a small threshold
    return np.abs(angle_sum - math.pi * 2) < 0.00000000001
########################################################################################
#
# closedNodeValues=[[0,0],[2,0],[2,1],[1,1],[1,2],[2,2],[2,3],[0,3],[0,0]]
# print(is_in_2d_polygon([1.01,1.01], closedNodeValues))