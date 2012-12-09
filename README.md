# Mobster is a tool that can help you get deeper understanding into the performance of mobile web applications on real mobile devices #

Mobster is built off of the WebKit framework and leverages real devices to extract data that can help you to measure and improve your mobile performance. Below are key features of Mobster

Highlights : 

 * Non-intrusive performance profiling of mobile web apps
 * Automatically detect regressions in page performance and memory usage
 * Insights into native browser events
 * Continuous integration with release process 

Mobster provides a simple way for developers to record crucial web performance data on mobile devices while running automated flows. Using Mobster, developers can test the performance of their site on a variety of devices and easily detect any performance regressions. You can gather following metrics from real devices using Mobster.

 * Page timings,network resource sizes and timings
 * Internal browser / DOM events like GC, paints, and CSS recalculates
 * HTTP waterfalls
 * Memory Utilization 


## Contribution ##

Mobster is a new project, and we are interested in building the community; we would welcome any thoughts or [patches](URL to be added). You can reach us [on the Apache mailing lists](http://incubator.apache.org/mobster/contact.html).

The Mobster code is available from git mirror:
 * git clone [https://github.com/linkedin/mobster]

## Getting Started ##

key components - 

 * WebKit Communicator - Handles low-level sending and receiving of messages. Provides a way to specify callbacks 
 * Remote WebKit Client - Uses WebKitCommunicator to provide an API for sending commands to the browser and querying for data (e.g. tell the browser to navigate to a URL, get CSS profiling results)
 * FlowProfiler - Interprets the flow file specified by the user and uses WebKitClient's API to perform the actions from the flow, while recording the results

### Using Mobster to measure performance of web applications on Android Device ###

Prerequisites - 

 * If you want to use Mobster to measure performance of web applications on a physical android device , you need to install Android SDK version 4.0 or later on your host.  You can download SDK here - http://developer.android.com/sdk/index.html#download
 * Download and install Python 2.6.6+ (but not Python 3) . 
 * You should download and install PIP, you can find instructions to download and install PIP here

1. Check out mobster code ( using git clone command)

2. Install the packages listed in requirements.txt

cd mobster
pip install -r requirements.txt

3. Open Chrome on your device. If using desktop Chrome, start it with remote debugging enabled and remote debugging port set to 9222, e.g. (for Mac OS):

<pre> open -a "Google Chrome" --args --remote-debugging-port=9222 --enable-memory-info </pre>

To test if the remote debugging is working try this on your chrome browser - http://localhost:9222. 

Note :
1. After you have executed the above command you should be able to see an instance of chrome browser
2. if "http://localhost:9222" is not working for you, try closing all instances of chrome browsers on your device before executing the command.

4. Connecting Mobster to Android device

 * Connect the device to your computer via USB
 * Enable USB debugging on the device in  settings -> Developer Options -> USB Debugging ( Please refer to your device manuals for details )
 * Open Chrome browser in the device and enable USB debugging in Settings -> Advanced -> Developer Tools -> Enable USB Web debugging
 * Execute the command below under the Android SDK folder : 	./<Android-SDK-Folder>/platform-tools/adb forward tcp:9222 localabstract:chrome_devtools_remote

5. Open Chrome on the device

6. Run the main Mobster script with a sample flow in your mobster home directory : 

<pre> 
'-d outputdir', help='Write JSON file to specified directory'
'-f filename', help='Used specified name for JSON file'
'-u urls', help='Comma separated URLs to profile'
'-t testfile', required=True, help='Use specified JSON test file to determine test actions'
'-i iterations', help='Do profiling task the specified number of times'
'-a average', action='store_true', help='Output the average results of the iterations'
'-p report', action='store_true', help='Call make_report.py to make a report and open it'

./bin/mobster.py -t sampleinput/sample.json -i 1 -a -p
</pre>

You should now be viewing the report in the browser. To learn how to make your own flows, look at the scripts in the bin/sampleinput/ directory.


### Using Mobster to measure performance of web applications on Desktop ###

Prerequisites - 

 * Download and install Python 2.6.6+ (but not Python 3) . 
 * You should download and install PIP, you can find instructions to download and install PIP here
 * You should install Chrome 18+ 

1. Check out mobster code ( using git clone command )

2. Install the packages listed in requirements.txt

cd mobster
pip install -r requirements.txt

3. Start Chrome on your desktop with remote debugging enabled and remote debugging port set to 9222:

Mac OS:

<pre> open -a "Google Chrome" --args --remote-debugging-port=9222 --enable-memory-info </pre>

Red Hat Linux (assuming google-chrome is in your PATH):

<pre> google-chrome --args --remote-debugging-port=9222 </pre>

To test if the remote debugging is working try this on your chrome browser - http://localhost:9222

4. Run the main Mobster script with a sample flow in your mobster home directory : 

<pre> ./bin/mobster.py -o data.json -t bin/sampleinput/sample.json </pre>

5. Generate a report with the collected data and open it in a browser:

<pre> ./bin/make_report.py -r data.json -b </pre>

You should now be viewing the report in the browser. To learn how to make your own flows, look at the scripts in the bin/sampleinput/ directory.

