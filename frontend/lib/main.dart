import 'package:flutter/material.dart';
import 'package:frontend/pages/home_page.dart';
import 'package:frontend/pages/setup_refrence_object.dart';
import 'package:frontend/pages/measure_item_page.dart';
import 'package:frontend/pages/scan_items.dart';
import 'package:frontend/pages/scan_storage_space.dart';
import 'package:frontend/pages/preferences_page.dart';
import 'package:frontend/pages/api_loader_page.dart';

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
      home: HomePage(),
      routes: {
        '/setupReferenceObject': (context) => SetupReferenceObject(),
        '/measureItem': (context) => MeasureItemPage(),
        '/scanItems': (context) => ScanItemsPage(),
        '/scanStorageSpace': (context) => ScanStorageSpacePage(),
        '/preferences': (context) => PreferencesPage(),
        '/apiLoaderPage': (context) => ApiLoaderPage(),
      },
    );
  }
}
