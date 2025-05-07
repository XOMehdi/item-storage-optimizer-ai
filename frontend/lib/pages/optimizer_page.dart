import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:developer';
import 'package:http/http.dart' as http;
import 'package:item_storage_optimizer_ai/models/measurement_results.dart';
import 'package:item_storage_optimizer_ai/pages/home_page.dart';

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

    log("Measurement Results: ${jsonEncode(MeasurementResults().data)}");

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

          log("Mapped placements: ${MeasurementResults().placements}");

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
