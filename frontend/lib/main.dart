import 'package:flutter/material.dart';
import 'package:item_storage_optimizer_ai/pages/home_page.dart';
import 'package:item_storage_optimizer_ai/pages/setup_refrence_object.dart';
import 'package:item_storage_optimizer_ai/pages/measure_item_page.dart';
import 'package:item_storage_optimizer_ai/pages/scan_items_page.dart';
import 'package:item_storage_optimizer_ai/pages/scan_storage_space_page.dart';
import 'package:item_storage_optimizer_ai/pages/optimizer_page.dart';
import 'package:item_storage_optimizer_ai/pages/preferences_page.dart';
import 'package:item_storage_optimizer_ai/pages/visualizer_page.dart';

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
        '/setupReferenceObjectPage': (context) => SetupReferenceObject(),
        '/measureItemPage': (context) => MeasureItemPage(),
        '/scanItemsPage': (context) => ScanItemsPage(),
        '/scanStorageSpacePage': (context) => ScanStorageSpacePage(),
        '/preferencesPage': (context) => PreferencesPage(),
        '/optimizerPage': (context) => OptimizerPage(),
        '/visualizerPage': (context) => VisualizerPage(),
      },
    );
  }
}
