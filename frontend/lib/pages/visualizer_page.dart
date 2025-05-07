import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:developer';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:item_storage_optimizer_ai/models/measurement_results.dart';

class VisualizerPage extends StatefulWidget {
  const VisualizerPage({super.key});

  @override
  State<VisualizerPage> createState() => _VisualizerPageState();
}

class _VisualizerPageState extends State<VisualizerPage> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();

    final placements = MeasurementResults().placements ?? [];

    log("visual placements: $placements");

    final container = MeasurementResults().data?['container'];

    final visualizerUrl = _generateVisualizerUrl(container, placements);

    _controller =
        WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..loadRequest(Uri.parse(visualizerUrl));
  }

  String _generateVisualizerUrl(
    Map<String, dynamic>? container,
    List<List<num>> placements,
  ) {
    if (container == null) return '';

    // Extract width, height, depth into a list
    final containerData = [
      container['width'] ?? 0,
      container['height'] ?? 0,
      container['depth'] ?? 0,
    ];

    final encodedContainer = Uri.encodeComponent(jsonEncode(containerData));
    final encodedPlacements = Uri.encodeComponent(jsonEncode(placements));

    return 'https://xomehdi.github.io/item-storage-optimizer-ai/index.html?container=$encodedContainer&placements=$encodedPlacements';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            'Visualizer',
            style: TextStyle(
              color: Colors.black,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
      body: WebViewWidget(controller: _controller),
    );
  }
}
