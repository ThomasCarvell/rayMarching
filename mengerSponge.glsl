#shader vertex
#version 460 core

layout(location = 0) in vec2 aPos;

out vec2 pos;

void main() {
    gl_Position = vec4(aPos,0.0,1.0);
    pos = aPos;
    return;
}







#shader fragment
#version 460 core

in vec2 pos;
out vec4 fragColor;

const float CASTTHRESHOLD = 0.001;
const float AMBIENCE = 0.02;
const float SHADOWRAYHEADSTART = 0.001;
const float MAXIMUMDISTANCE = 1000;
const int MAXNUMLIGHTS = 10;
const int MAXNUMREFLECTIONS = 5;

uniform vec2 fov;
uniform vec2 camRot;
uniform vec3 camPos;

struct light {
    vec3 pos;
    vec3 color;
    float intensity;
};

uniform int numLights = 1;
uniform light lights[MAXNUMLIGHTS];


struct sdfResult {
    float dist;
    vec3 color;
    float ref;
};

struct rayCastResult {
    float dist;
    bool collision;
    vec3 color;
    vec3 pos;
    float finalDist;
    float ref;
};

float sdBox( vec3 p, vec3 b )
{
    vec3 q = abs(p) - b;
    return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

sdfResult SDF(vec3 pos) {
    if (pos.x > 0.1) {
        pos.x = 0.2-pos.x;
    }

    sdfResult result;

    float dist1 = sdBox(pos-vec3(0.05,0.05,0.05),vec3(0.05,0.05,0.05));
    
    result.dist = dist1;
    result.ref = 0;
    result.color = vec3(1,1,1);
    return result;
}

vec3 calculateNormal(vec3 pos) {
    vec2 stp = vec2(0.0001,0.0);

    float gradX = SDF(pos+stp.xyy).dist-SDF(pos-stp.xyy).dist;
    float gradY = SDF(pos+stp.yxy).dist-SDF(pos-stp.yxy).dist;
    float gradZ = SDF(pos+stp.yyx).dist-SDF(pos-stp.yyx).dist;

    return normalize(vec3(gradX,gradY,gradZ));
}

rayCastResult castRay(vec3 ro, vec3 rd, float targetDist, int maxSteps = 100, int minSteps = 0, bool stepLimitCollision = false) {

    sdfResult delta;

    rayCastResult result = {0, stepLimitCollision, vec3(0,0,0), ro, 0, 0};

    for (int i = 0; i < maxSteps; i++) {
        delta = SDF(ro);
        ro += delta.dist * rd;
        result.dist += delta.dist;

        if (i > minSteps-1 && delta.dist < CASTTHRESHOLD) {
            result.collision = true;
            result.color = delta.color;
            result.finalDist = SDF(ro).dist;
            result.ref = delta.ref;
            break;
        }

        if (result.dist > targetDist) {
            result.collision = false;
            break;
        }
    }

    result.pos = ro;

    return result;
}


// rays are cast towards each light in the scene, the intensities of each light is recorded and a sum their colours is taken based on this
vec3 calculateLighting(vec3 reCastPos, vec3 normal) {
    vec3 sigmaColor = vec3(0,0,0);
    float intensity;

    for (int light = 0; light < numLights; light++) {
        float lightDist = distance(lights[light].pos, reCastPos);
        vec3 lightDir = (lights[light].pos - reCastPos) / lightDist;

        rayCastResult lightRay = castRay(reCastPos, lightDir, lightDist, 200, 10, true);

        if (lightRay.collision) continue;

        lightDist /= lights[light].intensity;
        intensity = (1/(1+lightDist*lightDist)) * dot(normal, lightDir);

        sigmaColor += lights[light].color * intensity;
    }

    return sigmaColor;
}


void main() {
    vec3 cpos = camPos;

    // calculate the direction vector of this pixel of the screen relative to the camera position
    vec3 direction = normalize(vec3(pos.x*fov.x,pos.y*fov.y,1));

    mat3 yRotation = mat3(vec3(cos(-camRot.x),0,-sin(-camRot.x)),
                          vec3(0,1,0),
                          vec3(sin(-camRot.x),0,cos(-camRot.x)));

    mat3 xRotation = mat3 (vec3(1,0,0),
                           vec3(0,cos(camRot.y),sin(camRot.y)),
                           vec3(0,-sin(camRot.y),cos(camRot.y)));

    direction *= xRotation;
    direction *= yRotation;

    // define the default pixel color to be a gradient to sky blue based on direction y coordinate
    fragColor = vec4(direction.y * vec3(0.529, 0.809, 0.922), 1);

    // define the starting direction as the one we are looking at
    // the starting status as having moved 0 distance, not collided and looking at black, at camera position and having no finalDist
    // and all light is to be determined
    vec3 rd = direction;
    rayCastResult final = {0, false, vec3(0,0,0), cpos, 0, 0};
    float lightTBD = 1;

    rayCastResult temp;
    vec3 normal;
    vec3 recastPos;
    vec3 calcColor;

    // iterate for all possible reflections
    for (int i = 0; i < MAXNUMREFLECTIONS+1; i++) {
        temp = castRay(final.pos, rd, MAXIMUMDISTANCE-final.dist, 200); // cast ray

        if (!temp.collision) break; // if there isn't a collision we are done

        normal = calculateNormal(temp.pos);
        recastPos = temp.pos + normal * (CASTTHRESHOLD - temp.finalDist + SHADOWRAYHEADSTART);

        if (temp.ref != 1) calcColor = max(calculateLighting(recastPos, normal),vec3(AMBIENCE)) * temp.color; // if we are not completely reflecting, calculate the color of the surface

        final.color += calcColor * ((1-temp.ref) * lightTBD);
        lightTBD *= temp.ref;

        if (lightTBD == 0) break; // if we have determined all light (hit an opaque object) we can exit

        rd = reflect(rd,normal); // reflect the ray direction off the normal
        final.pos = recastPos; // set the enxt start position to the recast position
        final.dist += temp.dist; // increment the total distance
    }

    if (lightTBD != 0) {
        final.color += lightTBD * rd.y * vec3(0.529, 0.809, 0.922); // if we exit without a terminating collision, the color to be determined is set to the sky color
    }

    fragColor = vec4(final.color, 1);
}

