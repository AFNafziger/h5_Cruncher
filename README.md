 _     _____   _____                       _               
| |   |  ___| /  __ \                     | |              
| |__ |___ \  | /  \/_ __ _   _ _ __   ___| |__   ___ _ __ 
| '_ \    \ \ | |   | '__| | | | '_ \ / __| '_ \ / _ \ '__|
| | | /\__/ / | \__/\ |  | |_| | | | | (__| | | |  __/ |   
|_| |_\____/   \____/_|   \__,_|_| |_|\___|_| |_|\___|_|                                                     
                                                           

***Project Description***

h5 Cruncher is a useful tool for converting huge hierarchical data files into more usable CSV data sets. It takes specified columns and rows of data from users in a simple design process and chunk loads them into a CSV. 

***How to Start?***

If you are on the SCC, start up a Desktop via SCC OnDemand's Interactive Apps. Connect to the desktop and open a terminal. Navigate to the davey-lab directory or the davey-lab/h5_Cruncher directory and type the command:

./run_h5cruncher.sh 

If this does not work for some reason you can access it by running it yourself. You will need to update your Python before you can use h5_Cruncher. In your terminal, navigate to /projectnb/davey-lab/h5_Cruncher using the change directory command (cd). Once in the /h5_Cruncher directory, run the command:

module load python3/3.12.4

<!> If you have not previously run the program or installed the modules h5py, numpy, and ttkbootstrap. You must install them:

pip install h5py numpy ttkbootstrap

Finally, run the following command to launch the program:

python main.py

***What to do?***

h5_Cruncher has various uses. It can be used to explore the unintuitive structure of h5 files as well as export portions or special selections of them to CSV files. To explore the structure of an h5 file, load the file in the File Upload window and click around on the data frames that appear below. Files that appear GREEN are exportable data frames, files that appear BLUE may inform the column names of exportable data frames that do not include them.

h5_Cruncher can be used to create large CSV files from h5 data, which can allow for easier use of data for research. Along with the conversion, it also allows users to specify what columns and data they want to include in the CSV. For example, a user can just use a portion of the features from OPS data and only the first 1000 rows of data. Users can do this by clicking on highlighted (green) data frames and selecting the Export button. From here, users can select what features and data they would like in their CSV and preview or export it using the buttons at the bottom of the window. Alternatively, users can press the specific instance button after loading an h5 file and create a CSV where a specified column has a specified value. 

<!> If planning to use datasets in Excel or other software, confirm the maximum data frame size usable by your planned application
<!> With large exports (around a million rows), exporting may take some time, especially on limited core usage from SCC

When exporting, data frames are split into smaller chunks and compiled into a CSV to avoid exploding your computer before being recombined into the final CSV.

