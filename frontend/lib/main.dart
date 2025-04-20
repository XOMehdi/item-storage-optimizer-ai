import 'package:flutter/material.dart';
import 'pages/home.dart';
import 'pages/scan_items.dart';
import 'pages/scan_storage_space.dart';
import 'pages/Preferences.dart';
import 'pages/setup_refrence_object.dart';
import 'pages/visualizer_page.dart';


void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Poppins',
        scaffoldBackgroundColor: const Color(0xffF7F8F8),
        appBarTheme: const AppBarTheme(
          color: Colors.white,
          elevation: 0.0,
          iconTheme: IconThemeData(color: Colors.black),
          titleTextStyle: TextStyle(
            color: Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(fontSize: 16, color: Colors.black87),
        ),
      ),
      // home: HomePage(),
      home: VisualizerPage(
        items: [
          [0, 0, 0, 10, 10, 10],
          [10, 0, 0, 10, 10, 10],
          [0, 10, 0, 10, 10, 10],
          [10, 10, 0, 10, 10, 10],
          [20, 0, 0, 8, 8, 8],
          [28, 0, 0, 12, 5, 10],
          [0, 0, 10, 5, 5, 10],
          [5, 0, 10, 10, 8, 15],
          [15, 0, 10, 10, 12, 10],
          [0, 20, 0, 15, 8, 12],
          [20, 8, 0, 10, 12, 15],
          [0, 0, 25, 30, 5, 5],
          [15, 20, 15, 10, 10, 10],
          [25, 20, 0, 10, 8, 15],
          [30, 0, 15, 10, 15, 10]
        ],
      ),
      routes: {
        '/setupReferenceObject': (context) => SetupReferenceObject(),
        '/scanItems': (context) => ScanItemsPage(),
        '/scanStorageSpace': (context) => ScanStorageSpacePage(),
        '/Preferences': (context) => PreferencesPage(),
      },
    );
  }
}
