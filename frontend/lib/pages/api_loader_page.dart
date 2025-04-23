import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'visualizer_page.dart';

class ApiLoaderPage extends StatefulWidget {
  const ApiLoaderPage({super.key});

  @override
  State<ApiLoaderPage> createState() => _ApiLoaderPageState();
}

class _ApiLoaderPageState extends State<ApiLoaderPage> {
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchDataFromApi();
  }

  Future<void> _fetchDataFromApi() async {
    const apiUrl = "https://optimizer.up.railway.app/optimize"; // Your actual API URL

    final payload = {
      "container": {"width": 30, "height": 20, "depth": 10},
      "items": [
        {
          "id": 1,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 2,
          "dimensions": {"width": 4, "height": 2, "depth": 1},
        },
        {
          "id": 3,
          "dimensions": {"width": 4, "height": 2, "depth": 1},
        },
        {
          "id": 4,
          "dimensions": {"width": 4, "height": 2, "depth": 1},
        },
        {
          "id": 5,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 6,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 7,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 8,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 9,
          "dimensions": {"width": 6, "height": 6, "depth": 2},
        },
        {
          "id": 10,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 11,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 12,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 13,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 14,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 15,
          "dimensions": {"width": 16, "height": 8, "depth": 1},
        },
        {
          "id": 16,
          "dimensions": {"width": 24, "height": 12, "depth": 9},
        },
        {
          "id": 17,
          "dimensions": {"width": 9, "height": 25, "depth": 7},
        },
      ],
      "config": {"population_size": 30, "generations": 50},
    };

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final jsonResponse = jsonDecode(response.body);
        if (jsonResponse['status'] == 'success' || jsonResponse['status'] == 'failure') {
          final List placements = jsonResponse['placements'];
          if (!mounted) return;
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => VisualizerPage(
                placements: placements.map<List<num>>((e) => List<num>.from(e)).toList(),
              ),
            ),
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
