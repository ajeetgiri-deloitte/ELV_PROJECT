========================
BUILD OUTPUT DESCRIPTION
========================

When you build an Java application project that has a main class, the IDE
automatically copies all of the JAR
files on the projects classpath to your projects dist/lib folder. The IDE
also adds each of the JAR files to the Class-Path element in the application
JAR files manifest file (MANIFEST.MF).

To run the project from the command line, go to the dist folder and
type the following:

java -jar "Final_ED_Both.jar" 

To distribute this project, zip up the dist folder (including the lib folder)
and distribute the ZIP file.

Notes:

* If two JAR files on the project classpath have the same name, only the first
JAR file is copied to the lib folder.
* Only JAR files are copied to the lib folder.
If the classpath contains other types of files or folders, these files (folders)
are not copied.
* If a library on the projects classpath also has a Class-Path element
specified in the manifest,the content of the Class-Path element has to be on
the projects runtime path.
* To set a main class in a standard Java project, right-click the project node
in the Projects window and choose Properties. Then click Run and enter the
class name in the Main Class field. Alternatively, you can manually type the
class name in the manifest Main-Class element.



Steps to encrypt the data and generate all the input parameter
-------------------------------------------------------------------
java -jar Final_ED_Both.jar arg1 arg2 arg3 arg4 arg5 arg6 arg7

where...
arg1 = Encrypt
arg2 = path to the xyz.txt file containing JSON data.(Ex.   D:\\My_Folder\\Json_Data.txt)
arg3 = path of the sessionkey.txt which will contain unique session key(Ex.   D:\\My_Folder\\sessionkey.txt)
arg4 = path of the encrypted_sessionkey.txt which will contain unique session key(Ex.   D:\\My_Folder\\encrypted_sessionkey.txt)
arg5 = path of the encrypted_json_data.txt which will contain unique session key(Ex.   D:\\My_Folder\\encrypted_json_data.txt)
arg6 = path of the encrypted_hashof_json_data.txt which will contain unique session key(Ex.   D:\\My_Folder\\encrypted_hashof_json_data.txt)
arg7 = path to the certificate.cer file (Public key)(Ex.   D:\\My_Folder\\certificate.cer)




Steps to Decrypt the data and generate all the output parameter
-------------------------------------------------------------------
java -jar Final_ED_Both.jar arg1 arg2 arg3 arg4

where...
arg1 = Decrypt
arg2 = path to the xyz.txt file containing Encrypted Signed data.(Ex.   D:\\My_Folder\\Encrypted_Signed_Data.txt)
arg3 = path to the sessionkey.txt file, which will hold the unique session key.(Ex.   D:\\My_Folder\\sessionkey.txt)
arg4 = path to the output file which will contain the decrypted signed data.  (Ex.   D:\\My_Folder\\Decrypted_Signed_Data.txt)