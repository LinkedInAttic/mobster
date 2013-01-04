# Mobster #

Mobster is a tool that can help you get deeper understanding into the performance of mobile web applications on real mobile devices.

It is built off of the WebKit remote debugging protocol and can leverage real devices to extract data that can help you to measure and improve your mobile performance. Below are key features of Mobster.

Highlights : 

 * Non-intrusive performance profiling of mobile web apps
 * Automatically detect regressions in page performance and memory usage
 * Insights into native browser events
 * Continuous integration with release process 

Mobster provides a simple way for developers to record crucial web performance data on mobile devices while running automated flows. Using Mobster, developers can test the performance of their site on a variety of devices and easily detect any performance regressions. You can gather following metrics from real devices using Mobster:

 * Page timings, network resource sizes and timings
 * Internal browser / DOM events like GC, paints, and CSS recalculates
 * HTTP waterfalls
 * Memory Utilization 

## Getting Started ##

### Prerequisites ###

1. Check out Mobster code:

    <pre>git clone https://github.com/armanhb/mobster.git</pre>

2. If you haven't already, install Python. You will need Python 2.6.6 or newer (but not Python 3). 

    To find the version of Python installed: 
    <pre>python --version</pre>

3. Install [PIP](http://www.pip-installer.org/en/latest/installing.html).

4. Install the necessary Python libraries using PIP.

    <pre>cd mobster; pip install -r requirements.txt</pre>


#### Android-Specific Prerequisites ####
1. You must have an Android device with Chrome installed. This will require Android 4.0 ICS or newer. Make sure you are running a recent version of the Chrome app.

2. Install the [Android SDK](http://developer.android.com/sdk/index.html#download) with packages corresponding to the version of Android your device is running.

3. Enable USB debugging on the device (Settings -> Developer Options -> USB Debugging, see your device manual for details)

4. In the Chrome settings, enable USB Debugging (Advanced -> Developer Tools -> Enable USB Web Debugging)

### Run Mobster with an Android Device ###

1. Execute the command below under the Android SDK folder:

    <pre>
    ./&lt;Android-SDK-Folder&gt;/platform-tools/adb forward tcp:9222 localabstract:chrome_devtools_remote
    </pre>

2. Open Chrome on the device if it isn't already open. Note that **Mobster will clear cookies** and other browsing data. The tab currently being viewed will be used by Mobster to navigate to webpages.

3. Run the main Mobster script with a sample flow in your Mobster home directory. This step is the same whether you are running Mobster with an Android device or desktop browser. 

    <pre>./bin/mobster.py -t bin/sampleinput/sample.json -p -b</pre>

Mobster reports will be generated under report folder if no folder is specified. Use "mobster.py -h" option to learn more. To learn how to make your own flows, look at the JSON files in the bin/sampleinput/ directory.


### Run Mobster with Desktop Chrome ###

1. Close all Chrome windows. Then, start desktop Chrome with remote debugging enabled and remote debugging port set to 9222:

    Mac OS:
    <pre> open -a "Google Chrome" --args --remote-debugging-port=9222 --enable-memory-info</pre>

    Red Hat Linux (assuming google-chrome is in your PATH):
    <pre> google-chrome --remote-debugging-port=9222 </pre>

    Windows (assuming chrome.exe is in your PATH):
    <pre> chrome --remote-debugging-port=9222 </pre>

    This should open a Chrome browser window. To test if remote debugging is working, navigate to http://localhost:9222 in your browser and verify that a page is displayed with the title "Inspectable Pages". If not, make sure that no Chrome windows are open and then try this command again.

2. Run the main Mobster script with a sample flow in your Mobster home directory. This step is the same whether you are running Mobster with an Android device or desktop browser. 

    <pre>./bin/mobster.py -t bin/sampleinput/sample.json -p -b</pre>

    Mobster reports will be generated in report folder if no folder is specified. Use "mobster.py -h" option to learn more. To learn how to make your own flows, look at the scripts in the bin/sampleinput/ directory.

**Important Note:**
If you use Chrome as your web browser normally, it will be annoying to run Mobster with Chrome because Mobster by default uses one of the currently open tab(s) for testing and also clears cookies, etc. This means that, at the end of a test, one of your open tab(s) will be showing the final web page from your test and you will be logged out of all websites. **An easy way to avoid this problem is to run Mobster with [Chromium](http://www.chromium.org/Home) or [Chrome Canary](https://www.google.com/intl/en/chrome/browser/canary.html) so your normal browsing is not affected.** Chrome, Chromium, and Chrome Canary can all be installed side-by-side.


## Contribution ##

Mobster is a new project, and we are interested in building the community; we would welcome any thoughts or [patches](https://github.com/linkedin/mobster/issues). You can reach us [on the Apache mailing lists](http://incubator.apache.org/mobster/contact.html).

The Mobster code is available from git mirror:
<pre>git clone https://github.com/linkedin/mobster</pre>

Key Components - 

 * WebKit Communicator - Handles low-level sending and receiving of messages. Provides a way to specify callbacks 
 * Remote WebKit Client - Uses WebKitCommunicator to provide an API for sending commands to the browser and querying for data (e.g. tell the browser to navigate to a URL, get CSS profiling results)
 * FlowProfiler - Interprets the flow file specified by the user and uses WebKitClient's API to perform the actions from the flow, while recording the results

