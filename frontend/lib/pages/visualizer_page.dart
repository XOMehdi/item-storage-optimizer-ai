import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class VisualizerPage extends StatefulWidget {
  final List<List<num>> items;

  const VisualizerPage({super.key, required this.items});

  @override
  State<VisualizerPage> createState() => _VisualizerPageState();
}

class _VisualizerPageState extends State<VisualizerPage> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();

    final visualizerUrl = _generateVisualizerUrl(widget.items);

    _controller =
        WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..loadRequest(Uri.parse(visualizerUrl));
  }

  String _generateVisualizerUrl(List<List<num>> items) {
    final encodedData = Uri.encodeComponent(jsonEncode(items));
    return 'https://xomehdi.github.io/item-storage-optimizer-ai/index.html?data=$encodedData';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Visualizer")),
      body: WebViewWidget(controller: _controller),
    );
  }
}
