import AppKit
let args = CommandLine.arguments
let dir = args[1], out = args[2]
let files = try! FileManager.default.contentsOfDirectory(atPath: dir).filter{$0.hasSuffix(".jpg")}.sorted()
let cols = 6, w = 260, h = 190, lab = 22
let rows = (files.count + cols - 1) / cols
let W = cols*w, H = rows*(h+lab)
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: W, pixelsHigh: H, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor.white.setFill(); NSRect(x:0,y:0,width:W,height:H).fill()
for (i,f) in files.enumerated() {
  let c = i % cols, r = i / cols
  let x = c*w, y = H - (r+1)*(h+lab)
  if let img = NSImage(contentsOfFile: dir+"/"+f) {
    let s = img.size; let k = min(Double(w-6)/s.width, Double(h-6)/s.height)
    let dw = s.width*k, dh = s.height*k
    img.draw(in: NSRect(x: Double(x)+(Double(w)-dw)/2, y: Double(y+lab)+(Double(h)-dh)/2, width: dw, height: dh))
  }
  (f as NSString).deletingPathExtension.draw(at: NSPoint(x: x+6, y: y+4), withAttributes: [.font: NSFont.systemFont(ofSize: 14), .foregroundColor: NSColor.black])
}
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .jpeg, properties: [.compressionFactor: 0.7])!.write(to: URL(fileURLWithPath: out))
