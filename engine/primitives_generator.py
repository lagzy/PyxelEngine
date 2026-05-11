"""
Procedural primitive generation for Panda3D.
Generates basic 3D shapes (Cube, Sphere, Capsule) using Panda3D's core geometry classes.
"""

import math

from panda3d.core import (
    GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    GeomTriangles, Geom, GeomNode, NodePath,
    BitMask32, GeomEnums
)


class PrimitivesGenerator:
    """Generates procedural 3D primitives."""

    @staticmethod
    def create_cube(name="Cube"):
        """Create a 1x1x1 cube."""
        # Create vertex data
        vdata = GeomVertexData(name, GeomVertexFormat.getV3n3t2(), GeomEnums.UHStatic)
        vdata.setNumRows(24)  # 6 faces * 4 vertices

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        # Define cube vertices (1x1x1, centered at origin)
        # Front face (z = 0.5)
        vertex.addData3(-0.5, -0.5, 0.5)
        normal.addData3(0, 0, 1)
        texcoord.addData2(0, 0)

        vertex.addData3(0.5, -0.5, 0.5)
        normal.addData3(0, 0, 1)
        texcoord.addData2(1, 0)

        vertex.addData3(0.5, 0.5, 0.5)
        normal.addData3(0, 0, 1)
        texcoord.addData2(1, 1)

        vertex.addData3(-0.5, 0.5, 0.5)
        normal.addData3(0, 0, 1)
        texcoord.addData2(0, 1)

        # Back face (z = -0.5)
        vertex.addData3(0.5, -0.5, -0.5)
        normal.addData3(0, 0, -1)
        texcoord.addData2(0, 0)

        vertex.addData3(-0.5, -0.5, -0.5)
        normal.addData3(0, 0, -1)
        texcoord.addData2(1, 0)

        vertex.addData3(-0.5, 0.5, -0.5)
        normal.addData3(0, 0, -1)
        texcoord.addData2(1, 1)

        vertex.addData3(0.5, 0.5, -0.5)
        normal.addData3(0, 0, -1)
        texcoord.addData2(0, 1)

        # Top face (y = 0.5)
        vertex.addData3(-0.5, 0.5, 0.5)
        normal.addData3(0, 1, 0)
        texcoord.addData2(0, 0)

        vertex.addData3(0.5, 0.5, 0.5)
        normal.addData3(0, 1, 0)
        texcoord.addData2(1, 0)

        vertex.addData3(0.5, 0.5, -0.5)
        normal.addData3(0, 1, 0)
        texcoord.addData2(1, 1)

        vertex.addData3(-0.5, 0.5, -0.5)
        normal.addData3(0, 1, 0)
        texcoord.addData2(0, 1)

        # Bottom face (y = -0.5)
        vertex.addData3(-0.5, -0.5, -0.5)
        normal.addData3(0, -1, 0)
        texcoord.addData2(0, 0)

        vertex.addData3(0.5, -0.5, -0.5)
        normal.addData3(0, -1, 0)
        texcoord.addData2(1, 0)

        vertex.addData3(0.5, -0.5, 0.5)
        normal.addData3(0, -1, 0)
        texcoord.addData2(1, 1)

        vertex.addData3(-0.5, -0.5, 0.5)
        normal.addData3(0, -1, 0)
        texcoord.addData2(0, 1)

        # Right face (x = 0.5)
        vertex.addData3(0.5, -0.5, 0.5)
        normal.addData3(1, 0, 0)
        texcoord.addData2(0, 0)

        vertex.addData3(0.5, -0.5, -0.5)
        normal.addData3(1, 0, 0)
        texcoord.addData2(1, 0)

        vertex.addData3(0.5, 0.5, -0.5)
        normal.addData3(1, 0, 0)
        texcoord.addData2(1, 1)

        vertex.addData3(0.5, 0.5, 0.5)
        normal.addData3(1, 0, 0)
        texcoord.addData2(0, 1)

        # Left face (x = -0.5)
        vertex.addData3(-0.5, -0.5, -0.5)
        normal.addData3(-1, 0, 0)
        texcoord.addData2(0, 0)

        vertex.addData3(-0.5, -0.5, 0.5)
        normal.addData3(-1, 0, 0)
        texcoord.addData2(1, 0)

        vertex.addData3(-0.5, 0.5, 0.5)
        normal.addData3(-1, 0, 0)
        texcoord.addData2(1, 1)

        vertex.addData3(-0.5, 0.5, -0.5)
        normal.addData3(-1, 0, 0)
        texcoord.addData2(0, 1)

        # Create triangles
        tris = GeomTriangles(GeomEnums.UHStatic)

        # Front face
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)

        # Back face
        tris.addVertices(4, 5, 6)
        tris.addVertices(4, 6, 7)

        # Top face
        tris.addVertices(8, 9, 10)
        tris.addVertices(8, 10, 11)

        # Bottom face
        tris.addVertices(12, 13, 14)
        tris.addVertices(12, 14, 15)

        # Right face
        tris.addVertices(16, 17, 18)
        tris.addVertices(16, 18, 19)

        # Left face
        tris.addVertices(20, 21, 22)
        tris.addVertices(20, 22, 23)

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node
        node = GeomNode(name)
        node.addGeom(geom)

        # Create NodePath and set collision mask for raycasting (bit 0 for picker)
        nodepath = NodePath(node)
        nodepath.setCollideMask(BitMask32.bit(1))
        nodepath.setPythonTag("selectable", True)

        return nodepath

    @staticmethod
    def create_sphere(name="Sphere", segments=16):
        """Create a UV sphere with given number of segments."""
        # Create vertex data
        num_vertices = (segments + 1) * (segments + 1)
        vdata = GeomVertexData(name, GeomVertexFormat.getV3n3t2(), GeomEnums.UHStatic)
        vdata.setNumRows(num_vertices)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        # Generate vertices
        for i in range(segments + 1):
            lat = (i / segments) * 3.14159265359
            sin_lat = math.sin(lat)
            cos_lat = math.cos(lat)

            for j in range(segments + 1):
                lon = (j / segments) * 2 * 3.14159265359
                sin_lon = math.sin(lon)
                cos_lon = math.cos(lon)

                x = sin_lat * cos_lon
                y = sin_lat * sin_lon
                z = cos_lat

                vertex.addData3(x * 0.5, y * 0.5, z * 0.5)
                normal.addData3(x, y, z)
                texcoord.addData2(j / segments, i / segments)

        # Create triangles
        tris = GeomTriangles(GeomEnums.UHStatic)

        for i in range(segments):
            for j in range(segments):
                first = i * (segments + 1) + j
                second = first + segments + 1

                tris.addVertices(first, second, first + 1)
                tris.addVertices(second, second + 1, first + 1)

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node
        node = GeomNode(name)
        node.addGeom(geom)

        # Create NodePath and set collision mask for raycasting (bit 0 for picker)
        nodepath = NodePath(node)
        nodepath.setCollideMask(BitMask32.bit(1))
        nodepath.setPythonTag("selectable", True)

        return nodepath

    @staticmethod
    def create_capsule(name="Capsule", segments=16, height=1.0, radius=0.25):
        """Create a capsule (cylinder with hemisphere caps)."""
        # Create vertex data
        # Top hemisphere + cylinder + bottom hemisphere
        num_rings_hemisphere = segments // 2
        num_rings_cylinder = 2
        total_rings = num_rings_hemisphere * 2 + num_rings_cylinder
        num_vertices = total_rings * (segments + 1)

        vdata = GeomVertexData(name, GeomVertexFormat.getV3n3t2(), GeomEnums.UHStatic)
        vdata.setNumRows(num_vertices)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        half_height = height / 2

        # Generate vertices
        ring = 0

        # Top hemisphere
        for i in range(num_rings_hemisphere):
            lat = (i / segments) * (3.14159265359 / 2)
            sin_lat = math.sin(lat)
            cos_lat = math.cos(lat)

            for j in range(segments + 1):
                lon = (j / segments) * 2 * 3.14159265359
                sin_lon = math.sin(lon)
                cos_lon = math.cos(lon)

                x = radius * sin_lat * cos_lon
                y = radius * sin_lat * sin_lon
                z = radius * cos_lat + half_height

                vertex.addData3(x, y, z)
                normal.addData3(sin_lat * cos_lon, sin_lat * sin_lon, cos_lat)
                texcoord.addData2(j / segments, i / total_rings)

        # Cylinder body
        for i in range(num_rings_cylinder):
            t = i / (num_rings_cylinder - 1) if num_rings_cylinder > 1 else 0
            z = half_height - t * height

            for j in range(segments + 1):
                lon = (j / segments) * 2 * 3.14159265359
                cos_lon = math.cos(lon)
                sin_lon = math.sin(lon)

                x = radius * cos_lon
                y = radius * sin_lon

                vertex.addData3(x, y, z)
                normal.addData3(cos_lon, sin_lon, 0)
                texcoord.addData2(j / segments, (num_rings_hemisphere + i) / total_rings)

        # Bottom hemisphere
        for i in range(num_rings_hemisphere):
            lat = (i / segments) * (3.14159265359 / 2)
            sin_lat = math.sin(lat)
            cos_lat = math.cos(lat)

            for j in range(segments + 1):
                lon = (j / segments) * 2 * 3.14159265359
                sin_lon = math.sin(lon)
                cos_lon = math.cos(lon)

                x = radius * sin_lat * cos_lon
                y = radius * sin_lat * sin_lon
                z = -radius * cos_lat - half_height

                vertex.addData3(x, y, z)
                normal.addData3(sin_lat * cos_lon, sin_lat * sin_lon, -cos_lat)
                texcoord.addData2(j / segments, (num_rings_hemisphere + num_rings_cylinder + i) / total_rings)

        # Create triangles
        tris = GeomTriangles(GeomEnums.UHStatic)

        for i in range(total_rings - 1):
            for j in range(segments):
                first = i * (segments + 1) + j
                second = first + segments + 1

                tris.addVertices(first, second, first + 1)
                tris.addVertices(second, second + 1, first + 1)

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node
        node = GeomNode(name)
        node.addGeom(geom)

        # Create NodePath and set collision mask for raycasting (bit 0 for picker)
        nodepath = NodePath(node)
        nodepath.setCollideMask(BitMask32.bit(1))
        nodepath.setPythonTag("selectable", True)

        return nodepath
