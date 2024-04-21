# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-04-21 17:44
"""
from OnvifClient import OnvifClient
from OnvifClient.PTZ import PTZ


def test_ptz(client: OnvifClient):
    ptz = PTZ(client)

    while True:
        # zoom in
        # ptz.zoom(1.0, 2)
        # zoom out
        print("开始缩小")
        ptz.zoom(-1.0, 2)
        ptz.zoom(-1.0, 2)
        ptz.zoom(-1.0, 2)

        print("开始放大")
        ptz.zoom(1.0, 2)

    # move down
    ptz.move_x(val=-1.0, timeout=2)

    time.sleep(10)
    ptz.move_x(val=1.0, timeout=2)
    time.sleep(10)

    exit(0)
    # Set preset
    # ptz.move_x(x=1.0, timeout=1)
    # ptz.set_preset('home')

    # move right -- (velocity, duration of move)
    ptz.move_x(val=1.0, timeout=2)

    # move left
    ptz.move_x(val=-1.0, timeout=2)

    # move down
    ptz.move_y(val=-1.0, timeout=2)

    # Move up
    ptz.move_y(val=1.0, timeout=2)

    # Absolute pan-tilt (pan position, tilt position, velocity)
    # DOES NOT RESULT IN CAMERA MOVEMENT
    ptz.move_absolute(x=-1.0, y=1.0, velocity=1.0)
    ptz.move_absolute(x=1.0, y=-1.0, velocity=1.0)

    # Relative move (pan increment, tilt increment, velocity)
    # DOES NOT RESULT IN CAMERA MOVEMENT
    # ptz.move_relative(0.5, 0.5, 8.0)

    # Get presets
    ptz.get_preset()
    # Go back to preset
    ptz.goto_preset('home')


if __name__ == '__main__':
    pass
