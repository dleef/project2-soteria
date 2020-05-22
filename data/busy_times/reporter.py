"""
reporter.py

===============================================================================

Last Modified: 21 May 2020
Modification By: Carter Perkins

Creation Date: 21 May 2020
Initial Author: Carter Perkins

===============================================================================

This module returns the relative "business" of a location, defined in the SDS
Section 4.1 - Busy Times Reporter, for scheduling and optimal time algorithms
utilized in the Flask API (aforementioned module is defined in the SDS Section
4.2 - Flask API). Due to this design, the Busy Times Reporter is completely
independent of all other modules.

In short, this reporting module utilizes two modes, accurate and simulated, to
determine how congested a particular location is. It utilizes the Google Maps
Place API for location data, and the 'Popular times' package to scrape the
Google Maps "Busy Times" information. Also, the simulated dataset is built
referencing the "Busy Times" data.
"""

# Standard Imports
import configparser
import enum
import os

# Third Party Packages
import populartimes

class BusyTimesReporter():
    """
    The BusyTimesReporter class serves as the interface for accessing location
    relative occupancy data. The preferred mode, accurate or simulated, can be
    passed at runtime (default simulated).
    """

    # Enum class to determine fetching mode
    class Mode(enum.Enum):
        SIMULATED = 0
        ACCURATE = 1

        @classmethod
        def has_value(cls, value):
            return value in cls._value2member_map_

    def get_api_key():
        """
        Returns the Google Maps API Key as specified in the 'credentials.ini'
        file (see README.md for more details).

        Ideally, this function would be private as the API_KEY should not be
        accessed outside of internal use of this interface.

        Returns:
            String              - Google Maps API Key
        Raises:
            FileNotFoundError   - Missing 'credentials.ini' file
            TypeError           - Malformed 'credentials.ini'
        """

        config = configparser.ConfigParser()

        # Cannot find credentials.ini file, raise error
        if not os.path.isfile("credentials.ini"):
            raise FileNotFoundError("credentials.ini")

        # Read from credentials.ini (root directory)
        config.read("credentials.ini")
        API_KEY = None
        try:
            API_KEY = config.get("DEFAULT", "GoogleMapsAPIKey")
        except (configparser.NoOptionError, KeyError) as e:
            # Invalid credentials.ini
            raise TypeError("malformed 'credentials.ini'")

        return API_KEY

    @classmethod
    def get_busy_times(cls, location, mode):
        """
        Returns a set of intervals representing the busy times of a location.

        Arguments:
            location    (String)                        - Google Maps Place ID
            mode        (Int or BusyTimesReporter.Mode) - Fetching Mode
        Returns:
            Dictionary                                  - Busy Times Intervals
                Key     (String)                        - Day of the Week
                Value   (Int List)                      - Hour Occupancy Ratios
        Raises:
            TypeError                                   - Bad argument passed
            SystemError                                 - 'populartimes' failed
        """

        # Validate inputs
        if not isinstance(mode, int) and not isinstance(mode, cls.Mode):
            raise TypeError("argument 'mode' must be of type int or BusyTimesReporter.Mode")
        if isinstance(mode, int) and not cls.Mode.has_value(mode):
            raise TypeError("argument 'mode' is invalid")

        # Standardize input
        if isinstance(mode, int):
            mode = cls.Mode(mode)

        DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday")
        busy_times = dict.fromkeys(DAYS)

        # Fetch API Key
        API_KEY = cls.get_api_key()

        if mode == cls.Mode.ACCURATE:
            result = None

            # Ensure valid Google Maps Place ID
            try:
                result = populartimes.get_id(key, location)
            except populartime.crawler.PopulartimesException:
                raise TypeError("argument 'location' is not a valid Google Maps Place ID")

            # Validate web crawler data from 'populartimes'
            for entry in result["populartimes"]:
                failure_flag = False
                # Must have an entry for each hour of the day
                if len(entry["data"]) != 24:
                    failure_flag = True
                else:
                    # Entry must be defined by date
                    if entry["name"] not in DAYS:
                        failure_flag = True
                    else:
                        for ratio in entry["data"]:
                            # Make sure entries are integers
                            if not isinstance(ratio, int):
                                failure_flag = True
                                break
                            else:
                                # Each ratio must be in [0, 100]
                                if ratio not in range(0, 101):
                                    failure_flag = True
                                    break
                if failure_flag:
                    raise SystemError("third party package 'populartimes' internally malformed")

                busy_times[entry["name"]] = entry["data"]
        else:
            # TODO: Simulated Mode
            pass

        return busy_times
