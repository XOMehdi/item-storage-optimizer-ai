import 'dart:developer';

import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/models/measurement_results.dart';
import 'package:frontend/pages/home_page.dart';

class OptimizerPage extends StatefulWidget {
  const OptimizerPage({super.key});

  @override
  State<OptimizerPage> createState() => _OptimizerPageState();
}

class _OptimizerPageState extends State<OptimizerPage> {
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchDataFromApi();
  }

  Future<void> _fetchDataFromApi() async {
    const apiUrl = "https://optimizer.up.railway.app/optimize";

    final payload = MeasurementResults().data;
    print(jsonEncode(MeasurementResults().data));

    // final payload = {
    //   "container": {"width": 30, "height": 20, "depth": 10},
    //   "items": [
    //     {
    //       "id": 1,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 2,
    //       "dimensions": {"width": 4, "height": 2, "depth": 1},
    //     },
    //     {
    //       "id": 3,
    //       "dimensions": {"width": 4, "height": 2, "depth": 1},
    //     },
    //     {
    //       "id": 4,
    //       "dimensions": {"width": 4, "height": 2, "depth": 1},
    //     },
    //     {
    //       "id": 5,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 6,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 7,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 8,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 9,
    //       "dimensions": {"width": 6, "height": 6, "depth": 2},
    //     },
    //     {
    //       "id": 10,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 11,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 12,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 13,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 14,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 15,
    //       "dimensions": {"width": 16, "height": 8, "depth": 1},
    //     },
    //     {
    //       "id": 16,
    //       "dimensions": {"width": 24, "height": 12, "depth": 9},
    //     },
    //     {
    //       "id": 17,
    //       "dimensions": {"width": 9, "height": 25, "depth": 7},
    //     },
    //   ],
    //   "config": {"population_size": 30, "generations": 50},
    // };

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final jsonResponse = jsonDecode(response.body);
        if (jsonResponse['status'] == 'success' ||
            jsonResponse['status'] == 'failure') {

           
          MeasurementResults().placements =
              (jsonResponse['placements'] as List)
                  .map<List<num>>((e) => List<num>.from(e))
                  .toList();

          print("Mapped placements: ${MeasurementResults().placements}");

          if (!mounted) return;
          showDialog(
            context: context,
            builder: (BuildContext context) {
              return AlertDialog(
                title: Text('Optimization Complete'),
                content: Text('The optimization process is finished.'),
                actions: <Widget>[
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (_) => HomePage()),
                      );
                    },
                    child: Text('OK'),
                  ),
                ],
              );
            },
          );
        } else {
          setState(() {
            _errorMessage =
                jsonResponse['message'] ?? "Unknown error occurred.";
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _errorMessage = "Error: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Request failed: $e";
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      body: Center(child: Text(_errorMessage ?? "Unknown error")),
    );
  }
}
